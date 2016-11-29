from __future__ import absolute_import, unicode_literals, print_function
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


class LogPolicy:
    LOG_NONE = 0
    LOG_LIVE = 1
    LOG_TOTAL = 2


@shared_task
def submit_job_to_server(job_pk, password, username=None, client=None,
                         log_policy=LogPolicy.LOG_LIVE, timeout=None):
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

    command = 'python -u {}'.format(job.remote_filename)
    if timeout is not None:
        command = 'timeout {}s {}'.format(timeout.total_seconds(), command)

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
