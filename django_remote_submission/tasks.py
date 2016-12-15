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


class ResultSet(object):
    def __init__(self, patterns):
        if patterns is None:
            patterns = ['*']

        self.patterns = patterns

    def filter(self, filenames):
        return [
            x
            for x in filenames
            if self.matches(x)
        ]

    def matches(self, filename):
        is_matching = False

        for pattern in self.patterns:
            if not pattern.startswith('!'):
                if fnmatch.fnmatch(filename, pattern):
                    is_matching = True
            else:
                if fnmatch.fnmatch(filename, pattern[1:]):
                    is_matching = False

        return is_matching


def deploy_key_if_it_doesnt_exist(client, public_key_filename):
    '''

    '''
    key = open(public_key_filename).read()
    client.exec_command('mkdir -p ~/.ssh/')

    command = '''
    KEY="%s"
    if [ -z "$(grep \"$KEY\" ~/.ssh/authorized_keys )" ];
    then
        echo $KEY >> ~/.ssh/authorized_keys;
        echo key added.;
    fi;
    '''%key

    stdin, stdout, stderr  = client.exec_command(command)
    logger.debug(stdout.readlines())
    logger.debug(stderr.readlines())

    client.exec_command('chmod 644 ~/.ssh/authorized_keys')
    client.exec_command('chmod 700 ~/.ssh/')

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


@shared_task
def submit_job_to_server(job_pk, password, username=None, client=None,
                         log_policy=LogPolicy.LOG_LIVE, timeout=None,
                         store_results=None):
    '''
    TODO: Refactoring!!
    '''

    job = Job.objects.get(pk=job_pk)

    if username is None:
        username = job.owner.username

    if client is None:
        client = start_client(client, job, username, password)

    sftp = client.open_sftp()
    sftp.chdir(job.remote_directory)
    sftp.putfo(six.StringIO(job.program), job.remote_filename)

    job.status = Job.STATUS.submitted
    job.save()

    command = '{} {}'.format(job.interpreter.path,job.remote_filename)
    if timeout is not None:
        command = 'timeout {}s {}'.format(timeout.total_seconds(), command)
    command='mkdir -p {0} && cd {0} && {1}'.format(job.remote_directory,command)

    transport = client.get_transport()
    channel = transport.open_session()

    logger.debug("Executing remotely the command: %s.", command)
    channel.exec_command(command)
    logger.debug("Executed...")
    done = False
    while not done:
        if channel.recv_ready():
            stream = channel.recv(1024).decode('utf-8')
            store_logs(stream,'stdout', log_policy, job)
        if channel.recv_stderr_ready():
            stream = channel.recv_stderr(1024).decode('utf-8')
            store_logs(stream,'stderr', log_policy, job)
        if channel.exit_status_ready():
            if channel.recv_exit_status() == 0:
                job.status = Job.STATUS.success
            else:
                job.status = Job.STATUS.failure
            job.save()
            done = True

    global all_lines
    if log_policy == LogPolicy.LOG_TOTAL:
        if all_lines['stdout']:
            Log.objects.create(
                content='\n'.join(all_lines['stdout']),
                stream='stdout',
                job=job,
            )
            all_lines['stdout'] = []
        if all_lines['stderr']:
            Log.objects.create(
                content='\n'.join(all_lines['stderr']),
                stream='stderr',
                job=job,
            )
            all_lines['stderr'] = []

    file_attrs = sftp.listdir_attr()
    file_map = { attr.filename: attr for attr in file_attrs }
    script_attr = file_map[job.remote_filename]
    script_mtime = script_attr.st_mtime

    result_set = ResultSet(patterns=store_results)
    results = []
    for attr in file_attrs:
        if attr is script_attr:
            continue

        if attr.st_mtime < script_mtime:
            continue

        if not result_set.matches(attr.filename):
            continue

        result = Result.objects.create(
            remote_filename=attr.filename,
            job=job,
        )

        with sftp.open(attr.filename, 'rb') as f:
            result.local_file.save(attr.filename, File(f), save=True)

        results.append(result)

    client.close()
    return results


def start_client(client, job, username, password=None,
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
