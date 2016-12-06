from __future__ import absolute_import, unicode_literals, print_function
from six import with_metaclass

import logging

logger = logging.getLogger(__name__)

import io
import os.path
import select
import socket

import six
from paramiko.client import SSHClient, AutoAddPolicy

from .models import Log, Job

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


class CommandMeta(type):
    '''
    Commands available in analysis.sns.gov
    (except for python3!)
    '''
    defaults = {
        'python' : '/usr/bin/python -u',
        'python2' : '/usr/bin/python2 -u',
        'python2.7' : '/usr/bin/python2.7 -u',
        'python3' : '/usr/bin/python3 -u',
        'python3.4' : '/usr/bin/python3.4 -u',
        'python3.5' : '/usr/bin/python3.5 -u',
        'bash' : '/usr/bin/bash',
        'sh' : '/bin/sh',
        'mantidpython' : '/usr/bin/mantidpython38 -u',
        'mantidpython35' : '/usr/bin/mantidpython35 -u',
        'mantidpython36' : '/usr/bin/mantidpython36 -u',
        'mantidpython37' : '/usr/bin/mantidpython37 -u',
        'mantidpython38' : '/usr/bin/mantidpython38 -u',
        'mantidpythonnightly' : '/usr/bin/mantidpythonnightly -u',
    }
    def __getitem__(cls,key):
        '''
        The default of get item is the key if val not found
        '''
        val = cls.defaults.get(key,key)
        return val

class Command(with_metaclass(CommandMeta)):
    '''
    In the code just call
        In [10]: Command['python']
        Out[10]: '/usr/bin/python -u'
    or:
        In [4]: Command.build_command('python',60)
        Out[4]: 'timeout 60s /usr/bin/python -u XX'
    '''
    @staticmethod
    def build_command(interpreter, timeout, job):
        command = '{} {}'.format(Command[interpreter],job.remote_filename)
        if timeout is not None:
            command = 'timeout {}s {}'.format(timeout.total_seconds(), command)
        return command

@shared_task
def submit_job_to_server(job_pk, password, username=None, client=None,
                         log_policy=LogPolicy.LOG_LIVE, timeout=None,
                         interpreter = 'python'):
    job = Job.objects.get(pk=job_pk)

    if username is None:
        username = job.owner.username

    if client is None:
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.connect(
            hostname=job.server.hostname,
            port=job.server.port,
            username=username,
            password=password,
        )

    sftp = client.open_sftp()
    sftp.chdir(job.remote_directory)
    sftp.putfo(six.StringIO(job.program), job.remote_filename)

    job.status = Job.STATUS.submitted
    job.save()

    command = Command.build_command(interpreter,timeout, job)
    logger.debug("Executing remotely teh command: %s.", command)

    stdin, stdout, stderr = client.exec_command(
        command='cd {} && {}'.format(
            job.remote_directory,
            command,
        ),
        bufsize=1,
    )

    channel = stdin.channel

    all_lines = []
    for line in stdout:
        if log_policy == LogPolicy.LOG_LIVE:
            Log.objects.create(
                content=line.strip('\n'),
                job=job,
            )

        elif log_policy == LogPolicy.LOG_TOTAL:
            all_lines.append(line.strip('\n'))

        elif log_policy == LogPolicy.LOG_NONE:
            pass

        else:
            msg = 'Unexpected value for log_policy: {!r}'.format(log_policy)
            raise ValueError(msg)

    if log_policy == LogPolicy.LOG_TOTAL:
        Log.objects.create(
            content='\n'.join(all_lines),
            job=job,
        )

    stdout.close()
    stderr.close()

    if channel.recv_exit_status() == 0:
        job.status = Job.STATUS.success
    else:
        job.status = Job.STATUS.failure

    job.save()

    file_attrs = sftp.listdir_attr()
    file_map = { attr.filename: attr for attr in file_attrs }
    script_attr = file_map[job.remote_filename]
    script_mtime = script_attr.st_mtime

    modified = []
    for attr in file_attrs:
        if attr is script_attr:
            continue

        if attr.st_mtime < script_mtime:
            continue

        modified.append(attr.filename)

    return modified
