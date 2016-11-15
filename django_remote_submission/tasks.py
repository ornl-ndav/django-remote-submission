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
        return func


@shared_task
def submit_job_to_server(job_pk, server, password, username=None, client=None):
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
    path = os.path.join(job.remote_directory, job.remote_filename)
    sftp.putfo(six.StringIO(job.program), path)

    job.status = Job.STATUS.submitted
    job.save()

    stdin, stdout, stderr = client.exec_command(
        command='python -u {}'.format(path),
        bufsize=1,
    )

    channel = stdin.channel

    for line in stdout:
        Log.objects.create(
            content=line.strip('\n'),
            job=job,
        )

    stdout.close()
    stderr.close()

    if channel.recv_exit_status() == 0:
        job.status = Job.STATUS.success
    else:
        job.status = Job.STATUS.failure

    job.save()
