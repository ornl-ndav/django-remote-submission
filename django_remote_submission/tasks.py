from __future__ import absolute_import, unicode_literals, print_function
import io
import os.path
import select
import socket

import six
from paramiko.client import SSHClient, AutoAddPolicy

from .models import Log

try:
    from celery import shared_task
except ImportError:
    def shared_task(func):
        return func


@shared_task
def submit_job_to_server(job, server, password, username=None, client=None):
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
    sftp.putfo(io.StringIO(six.u(job.program)), path)

    stdin, stdout, stderr = client.exec_command(
        command='python -u {}'.format(path),
        bufsize=1,
    )

    for line in stdout:
        Log.objects.create(
            content=line.strip('\n'),
            job=job,
        )

    stdout.close()
    stderr.close()
