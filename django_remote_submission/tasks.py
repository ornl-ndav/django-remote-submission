from __future__ import absolute_import, unicode_literals, print_function
import os
import sys
import logging

logger = logging.getLogger(__name__)

import io
import os.path
import select
import socket
import collections
import fnmatch

import six
from paramiko import (
    AuthenticationException, BadHostKeyException, AuthenticationException,
)
from paramiko.client import SSHClient, AutoAddPolicy
from threading import Thread
from django.core.files import File

from .models import Log, Job, Result, Interpreter
from .remote import RemoteWrapper

try:
    from celery import shared_task
except ImportError:
    logger.info('Could not import Celery. '
                'Tasks will not be implemented by Celery\'s queue.')

    def shared_task(func):
        def delay(*args, **kwargs):
            return func(*args, **kwargs)

        func.delay = delay
        return func


class LogPolicy(object):
    LOG_NONE = 0
    LOG_LIVE = 1
    LOG_TOTAL = 2


def is_matching(filename, patterns=None):
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


all_lines = {
    'stdout' : [],
    'stderr' : [],
}

def store_logs(stream, stream_type, log_policy, job):
    '''
    Store logs in the DB
    @param stream_type :: One of ('stdout','stderr')
    '''
    global all_lines

    for line in stream.split("\n"):
        line = line.strip("\n")
        if line:
            if log_policy == LogPolicy.LOG_LIVE:
                logger.debug("LOG_LIVE :: %s :: %s",stream_type,line)
                Log.objects.create(
                    content=line,
                    stream=stream_type,
                    job=job,
                )

            elif log_policy == LogPolicy.LOG_TOTAL:
                logger.debug("LOG_TOTAL :: %s :: %s",stream_type,line)
                all_lines[stream_type].append(line)

            elif log_policy == LogPolicy.LOG_NONE:
                logger.debug("LOG_NONE :: %s :: %s",stream_type,line)
                pass

            else:
                msg = 'Unexpected value for log_policy: {!r}'.format(log_policy)
                raise ValueError(msg)


class LogContainer(object):
    LogLine = collections.namedtuple('LogLine', [
        'now', 'output',
    ])

    def __init__(self, job, log_policy):
        self.job = job
        self.log_policy = log_policy
        self.stdout = []
        self.stderr = []

    def write(self, lst, now, output):
        lst.append(LogContainer.LogLine(
            now=now,
            output=output,
        ))

        if self.log_policy == LogPolicy.LOG_LIVE:
            self.flush()

    def write_stdout(self, now, output):
        self.write(self.stdout, now, output)

    def write_stderr(self, now, output):
        self.write(self.stderr, now, output)

    def flush(self):
        print('flush: {!r} {!r}'.format(self.stdout, self.stderr))

        if len(self.stdout) > 0:
            Log.objects.create(
                time=self.stdout[-1],
                content='\n'.join(line.output for line in self.stdout),
                stream='stdout',
                job=self.job,
            )

            del self.stdout[:]

        if len(self.stderr) > 0:
            Log.objects.create(
                time=self.stderr[-1].now,
                content='\n'.join(line.output for line in self.stderr),
                stream='stderr',
                job=self.job,
            )

            del self.stderr[:]


@shared_task
def submit_job_to_server(job_pk, password, username=None, timeout=None,
                         log_policy=LogPolicy.LOG_LIVE, store_results=None):
    job = Job.objects.get(pk=job_pk)

    if username is None:
        username = job.owner.username

    wrapper = RemoteWrapper(
        hostname=job.server.hostname,
        username=username,
        port=job.server.port,
    )

    logs = LogContainer(
        job=job,
        log_policy=log_policy,
    )

    with wrapper.connect(password):
        wrapper.chdir(job.remote_directory)

        with wrapper.open(job.remote_filename, 'wt') as f:
            f.write(job.program)

        job.status = Job.STATUS.submitted
        job.save()

        job_status = wrapper.exec_command(
            [job.interpreter.path, job.remote_filename],
            timeout=timeout,
            stdout_handler=logs.write_stdout,
            stderr_handler=logs.write_stderr,
        )

        logs.flush()

        file_attrs = wrapper.listdir_attr()
        file_map = { attr.filename: attr for attr in file_attrs }
        script_attr = file_map[job.remote_filename]
        script_mtime = script_attr.st_mtime

        results = []
        for attr in file_attrs:
            if attr is script_attr:
                continue

            if attr.st_mtime < script_mtime:
                continue

            if not is_matching(attr.filename, store_results):
                continue

            result = Result.objects.create(
                remote_filename=attr.filename,
                job=job,
            )

            with wrapper.open(attr.filename, 'rb') as f:
                result.local_file.save(attr.filename, File(f), save=True)

            results.append(result)

    return results


def start_client(job, username, password=None,
    public_key_filename=os.path.expanduser('~/.ssh/id_rsa.pub')):
    '''
    This starts an
    '''
    client = SSHClient()
    client.set_missing_host_key_policy(AutoAddPolicy())

    server_hostname = job.server.hostname
    server_port = job.server.port
    try:
        logger.info("Connecting to %s with public key.", server_hostname)
        client.connect(server_hostname, port=server_port, username=username,
            key_filename=public_key_filename)
    except (AuthenticationException, BadHostKeyException):
        try:
            if password is None:
                logger.error("Connection with public key failed! The password is mandatory")
                return None
            logger.info("Connecting to %s with password.", server_hostname)
            client.connect(server_hostname, port=server_port, username=username,
                password=password)
            deploy_key_if_it_doesnt_exist(client, public_key_filename)
        except AuthenticationException:
            logger.error("Authenctication error! Wrong password...")
            return None
    return client
