"""

"""

from __future__ import absolute_import, unicode_literals, print_function
import logging
import os
import textwrap
import datetime

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote

from paramiko import (
    AuthenticationException, BadHostKeyException,
)
from paramiko.client import SSHClient, AutoAddPolicy
from django.utils.timezone import now
import six

logger = logging.getLogger(__name__)


class LogPolicy(object):
    LOG_NONE = 0
    LOG_LIVE = 1
    LOG_TOTAL = 2


class RemoteWrapper(object):
    """

    """
    def __init__(self, hostname, username, port=22):
        self.hostname = hostname
        self.username = username
        self.port = port
        self._client = None
        self._sftp = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self, password=None, public_key_filename=None):
        self._client = self._start_client(password, public_key_filename)
        self._sftp = self._client.open_sftp()
        return self

    def close(self):
        self._sftp.close()
        self._sftp = None

        self._client.close()
        self._client = None

    def chdir(self, remote_directory):
        self._sftp.chdir(remote_directory)

    def open(self, filename, mode):
        return self._sftp.open(filename, mode)

    def listdir_attr(self):
        return self._sftp.listdir_attr()

    def exec_command(self, args, workdir, timeout=None, stdout_handler=None,
                     stderr_handler=None):
        chdir = self._make_command(['cd', workdir], None)
        run = self._make_command(args, timeout)
        command = '{} && {}'.format(chdir, run)
        print('exec_command(command={!r})'.format(command))

        transport = self._client.get_transport()
        channel = transport.open_session()

        channel.exec_command(command)
        while True:
            current_time = now()
            if channel.recv_ready():
                print('channel.recv_ready()')
                output = channel.recv(1024).decode('utf-8')
                stdout_handler(current_time, output)

            if channel.recv_stderr_ready():
                print('channel.recv_stderr_ready()')
                output = channel.recv_stderr(1024).decode('utf-8')
                stderr_handler(current_time, output)

            if channel.exit_status_ready():
                print('channel.exit_status_ready()')
                if channel.recv_ready() or channel.recv_stderr_ready():
                    print('try again')
                    continue

                if channel.recv_exit_status() == 0:
                    print('return True')
                    return True
                else:
                    print('return False')
                    return False

    def _start_client(self, password, public_key_filename):
        if public_key_filename is None:
            public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')

        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        server_hostname = self.hostname
        server_port = self.port

        try:
            logger.info("Connecting to %s with public key.", server_hostname)
            client.connect(
                server_hostname,
                port=server_port,
                username=self.username,
                key_filename=public_key_filename,
            )

        except (AuthenticationException, BadHostKeyException) as e:
            if password is None:
                logger.error("Connection with public key failed! "
                             "The password is mandatory")
                six.raise_from(ValueError('needs password'), e)

            try:
                logger.info("Connecting to %s with password.", server_hostname)
                client.connect(
                    server_hostname,
                    port=server_port,
                    username=self.username,
                    password=password,
                )
                deploy_key_if_it_doesnt_exist(client, public_key_filename)

            except AuthenticationException as e:
                logger.error("Authenctication error! Wrong password...")
                six.raise_from(ValueError('incorrect password'), e)

        return client

    def _make_command(self, args, timeout):
        command = ' '.join(cmd_quote(arg) for arg in args)

        if timeout is not None:
            command = 'timeout {}s {}'.format(timeout.total_seconds(), command)

        return command


def deploy_key_if_it_doesnt_exist(client, public_key_filename):
    """

    """
    with open(public_key_filename, 'rt', encoding='utf-8') as f:
        key = f.read()

    client.exec_command('mkdir -p ~/.ssh/')

    command = textwrap.dedent('''\
    KEY={}
    if [ -z "$(grep \"$KEY\" ~/.ssh/authorized_keys )" ]; then
        printf $'%s\n' "$KEY" >> ~/.ssh/authorized_keys
        echo key added.
    fi
    '''.format(shlex.quote(key)))

    stdin, stdout, stderr = client.exec_command(command)
    logger.debug(stdout.readlines())
    logger.debug(stderr.readlines())

    client.exec_command('chmod 644 ~/.ssh/authorized_keys')
    client.exec_command('chmod 700 ~/.ssh/')
