"""Submit a job to a remote server and handle logging.

This module can be used either with Celery, in which case it will run in a
background thread, or as a normal function call, in which case it will block
the current execution thread.

"""
from __future__ import absolute_import, print_function, unicode_literals

import collections
import fnmatch
import io
import os
import os.path
import select
import socket
import sys
import time
from threading import Thread

import six
from django.core.files import File
from paramiko import AuthenticationException, BadHostKeyException
from paramiko.client import AutoAddPolicy, SSHClient

from celery.utils.log import get_task_logger

from .models import Interpreter, Job, Log, Result
from .wrapper.local import LocalWrapper
from .wrapper.remote import RemoteWrapper

logger = get_task_logger(__name__)


try:
    from celery import shared_task
except ImportError:
    logger.warning('Could not import Celery. '
                   'Tasks will not be implemented by Celery\'s queue.')

    def shared_task(func):
        """Naive wrapper in case Celery does not exist."""
        def delay(*args, **kwargs):
            return func(*args, **kwargs)

        func.delay = delay
        return func


class LogPolicy(object):
    """Specify how logging should be done when running a job."""

    LOG_NONE = 0
    """Don't log anything from the running job."""

    LOG_LIVE = 1
    """Create Log objects immediately when they are received."""

    LOG_TOTAL = 2
    """Combine all of stdout and stderr at the end of the job."""


def is_matching(filename, patterns=None):
    """Check if a filename matches the list of positive and negative patterns.

    Positive patterns are strings like ``"1.txt"``, ``"[23].txt"``, or
    ``"*.txt"``.

    Negative patterns are strings like ``"!1.txt"``, ``"![23].txt"``, or
    ``"!*.txt"``.

    Each pattern is checked in turn, so the list of patterns ``["!*.txt",
    "1.txt"]`` will still match ``"1.txt"``.

    >>> from django_remote_submission.tasks import is_matching
    >>> is_matching("1.txt", patterns=["1.txt"])
    True
    >>> is_matching("1.txt", patterns=["[12].txt"])
    True
    >>> is_matching("1.txt", patterns=["*.txt"])
    True
    >>> is_matching("1.txt", patterns=["1.txt", "!*.txt"])
    False
    >>> is_matching("1.txt", patterns=["!*.txt", "[12].txt"])
    True

    """
    if patterns is None:
        patterns = ['*']

    is_matching = False

    for pattern in patterns:
        if not pattern.startswith('!'):
            if fnmatch.fnmatch(filename, pattern):
                is_matching = True
        else:
            if fnmatch.fnmatch(filename, pattern[1:]):
                is_matching = False

    return is_matching


class LogContainer(object):
    """Manage logs sent by a job according to the log policy.

    .. testsetup::

       from django_remote_submission.models import Job, Server, Interpreter
       from django.contrib.auth import get_user_model
       python3 = Interpreter(name='Python 3', path='/bin/python3', arguments=['-u'])
       server = Server(title='Remote', hostname='foo.invalid', port=22)
       user = get_user_model()(username='john')
       job = Job(title='My Job', program='print("hello world")',
           remote_directory='/tmp/', remote_filename='foobar.py',
           owner=user, server=server, interpreter=python3,
       )

    >>> from django_remote_submission.tasks import LogContainer, LogPolicy
    >>> from datetime import datetime
    >>> now = datetime(year=2017, month=1, day=2, hour=3, minute=4, second=5)
    >>> logs = LogContainer(job, LogPolicy.LOG_LIVE)
    >>> logs.write_stdout(now, 'hello world')  # doctest: +SKIP
    >>> Log.objects.get()  # doctest: +SKIP
    <Log: 2017-01-02 03:04:05 My Job>

    """

    LogLine = collections.namedtuple('LogLine', [
        'now', 'output',
    ])

    def __init__(self, job, log_policy):
        """Instantiate a log container.

        :param models.Job job: the job these logs are coming from
        :param LogPolicy log_policy: the policy to use for logging

        """
        self.job = job
        """The job that these logs are coming from."""

        self.log_policy = log_policy
        """The policy to use when logging."""

        self._stdout = []
        """The list of log lines that came from stdout."""

        self._stderr = []
        """The list of log lines that came from stderr."""

    def _write(self, lst, now, output):
        """Append the current log entry to the given list and flush.

        :param lst: either :attr:`stdout` or :attr:`stderr`
        :param datetime.datetime now: the time this line was produced
        :param str output: the line of output from the job

        """
        if self.log_policy != LogPolicy.LOG_NONE:
            lst.append(LogContainer.LogLine(
                now=now,
                output=output,
            ))

        if self.log_policy == LogPolicy.LOG_LIVE:
            self.flush()

    def write_stdout(self, now, output):
        """Write some output from a job's stdout stream.

        :param datetime.datetime now: the time this output was produced
        :param str output: the output that was produced

        """
        self._write(self._stdout, now, output)

    def write_stderr(self, now, output):
        """Write some output from a job's stderr stream.

        :param datetime.datetime now: the time this output was produced
        :param str output: the output that was produced

        """
        self._write(self._stderr, now, output)

    def flush(self):
        """Flush the stdout and stderr lists to Django models.

        If the :attr:`log_policy` is :const:`LogPolicy.LOG_TOTAL`, this method
        will need to be called at the end of the job to ensure all the data
        gets written out.

        There is no penalty for calling this method multiple times, so it can
        be called at the end of the job regardless of which log policy is used.

        """
        if len(self._stdout) > 0:
            Log.objects.create(
                time=self._stdout[-1].now,
                content=''.join(line.output for line in self._stdout),
                stream='stdout',
                job=self.job,
            )

            del self._stdout[:]

        if len(self._stderr) > 0:
            Log.objects.create(
                time=self._stderr[-1].now,
                content=''.join(line.output for line in self._stderr),
                stream='stderr',
                job=self.job,
            )

            del self._stderr[:]


@shared_task
def submit_job_to_server(job_pk, password=None, public_key_filename=None, username=None,
                         timeout=None, log_policy=LogPolicy.LOG_LIVE,
                         store_results=None, remote=True):
    """Submit a job to the remote server.

    This can be used as a Celery task, if the library is installed and running.

    :param int job_pk: the primary key of the :class:`models.Job` to submit
    :param str password: the password of the user submitting the job
    :param public_key_filename: the path where it is.
    :param str username: the username of the user submitting, if it is
        different from the owner of the job
    :param datetime.timedelta timeout: the timeout for running the job
    :param LogPolicy log_policy: the policy to use for logging
    :param list(str) store_results: the patterns to use for the results to store
    :param bool remote: Either runs this task locally on the host or in a remote server.

    """

    logger.debug("submit_job_to_server: %s", locals().keys())

    wrapper_cls = RemoteWrapper if remote else LocalWrapper

    job = Job.objects.get(pk=job_pk)

    if username is None:
        username = job.owner.username

    wrapper = wrapper_cls(
        hostname=job.server.hostname,
        username=username,
        port=job.server.port,
    )

    logs = LogContainer(
        job=job,
        log_policy=log_policy,
    )

    with wrapper.connect(password, public_key_filename):
        wrapper.chdir(job.remote_directory)

        with wrapper.open(job.remote_filename, 'wt') as f:
            f.write(job.program)

        time.sleep(1)

        job.status = Job.STATUS.submitted
        job.save()

        interp = job.interpreter.path
        workdir = job.remote_directory
        args = job.interpreter.arguments
        filename = job.remote_filename

        job_status = wrapper.exec_command(
            [interp] + args + [filename],
            workdir,
            timeout=timeout,
            stdout_handler=logs.write_stdout,
            stderr_handler=logs.write_stderr,
        )

        logs.flush()

        job.status = Job.STATUS.success if job_status else Job.STATUS.failure
        job.save()

        file_attrs = wrapper.listdir_attr()
        file_map = { attr.filename: attr for attr in file_attrs }
        script_attr = file_map[job.remote_filename]
        script_mtime = script_attr.st_mtime

        results = []
        for attr in file_attrs:
            # logger.debug('Listing directory: {!r}'.format(attr))

            if attr is script_attr:
                continue

            if attr.st_mtime < script_mtime:
                continue

            if not is_matching(attr.filename, store_results):
                # logger.debug('Listing directory: is_matching: {}'.format(attr.filename))
                continue
            else:
                # logger.debug('Listing directory: not is_matching: {}'.format(attr.filename))
                pass

            result = Result.objects.create(
                remote_filename=attr.filename,
                job=job,
            )

            with wrapper.open(attr.filename, 'rb') as f:
                result.local_file.save(attr.filename, File(f), save=True)

            results.append(result)

    return { r.remote_filename: r.pk for r in results }


@shared_task
def copy_key_to_server(username, password, hostname, port=22,
                       public_key_filename=None,
                       remote=True):
    """Copy the client key to the remote server so the next connections
    do not need the password any further

    This can be used as a Celery task, if the library is installed and running.
    
    :param str username: the username of the user submitting
    :param str password: the password of the user submitting the job
    :param str hostname: The hostname used to connect to the server
    :param int port: The port to connect to for SSH (usually 22)
    :param public_key_filename: the path where it is.
    :param bool remote: Either runs this task locally on the host or in a remote server.

    """
    
    wrapper_cls = RemoteWrapper if remote else LocalWrapper

    wrapper = wrapper_cls(
        hostname=hostname,
        username=username,
        port=port,
    )
    # wrapper_cls.hostname = hostname
    # wrapper_cls.username = username
    # wrapper_cls.port = port

    with wrapper.connect(password, public_key_filename):
        wrapper.deploy_key_if_it_does_not_exist()

    return None


@shared_task
def delete_key_from_server(username, password, hostname, port=22,
                           public_key_filename=None,
                           remote=True):
    """Delete the client key from the remote server so the next connections
    will need password. This can be used at the logout of the session.

    This can be used as a Celery task, if the library is installed and running.
    
    :param str username: the username of the user submitting
    :param str password: the password of the user submitting the job
    :param str hostname: The hostname used to connect to the server
    :param int port: The port to connect to for SSH (usually 22)
    :param public_key_filename: the path where it is.
    :param bool remote: Either runs this task locally on the host or in a remote server.

    """
   
    wrapper_cls = RemoteWrapper if remote else LocalWrapper

    wrapper = wrapper_cls(
        hostname=hostname,
        username=username,
        port=port,
    )

    with wrapper.connect(password, public_key_filename):
        wrapper.delete_key()

    return None
