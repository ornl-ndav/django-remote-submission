"""Provides a wrapper around Paramiko to simplify the API.

This module is meant to be a general wrapper so that a ``LocalWrapper`` can
also be created to run tests in continuous integration services where SSH is
not available.

"""

from __future__ import absolute_import, unicode_literals, print_function
import logging
import os
import textwrap
import datetime
import uuid

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


class RemoteWrapper(object):
    """Wrapper around Paramiko which simplifies the remote connection API.

    The goal with this class is to also be able to provide a ``LocalWrapper``
    which works with the local file system, so that tests can be run on
    continuous integration servers.

    """

    def __init__(self, hostname, username, port=22):
        """Initialize the wrapper.

        :param str hostname: the hostname of the server to connect to
        :param str username: the username of the user on the remote server
        :param int port: the SSH port to connect to

        """
        self.hostname = hostname
        self.username = username
        self.port = port

        self._client = None
        """The Paramiko Client instance"""

        self._sftp = None
        """The Paramiko SFTP instance"""

    def __enter__(self):
        """Allow the use of ``with wrapper:``."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Allow the use of ``with wrapper:``."""
        self.close()

    def connect(self, password=None, public_key_filename=None):
        """Connect to the remote host with the given password and public key.

        Meant to be used like::

            with wrapper.connect(password='password0'):
                pass

        :param str password: the password of the user on the remote server
        :param str public_key_filename: the file containing the public key

        """
        if public_key_filename is None:
            public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')

        self._public_key_filename = public_key_filename
        self._client = self._start_client(password, public_key_filename)
        self._sftp = self._client.open_sftp()
        return self

    def close(self):
        """Close any open connections and clear their attributes."""
        self._sftp.close()
        self._sftp = None

        self._client.close()
        self._client = None

    def chdir(self, remote_directory):
        """Change directories to the remote directory.

        :param str remote_directory: the directory to change to

        """
        self._sftp.chdir(remote_directory)

    def open(self, filename, mode):
        """Open a file from the last used remote directory.

        :param str filename: the name of the file to open
        :param str mode: the mode to use to open the file (see :func:`file`'s
            documentation for more information)

        """
        return self._sftp.open(filename, mode)

    def listdir_attr(self):
        """Retrieve a list of files and their attributes.

        Each object is guaranteed to have a ``filename`` attribute as well as
        an ``st_mtime`` attribute, which gives the last modified time in
        seconds.

        """
        return self._sftp.listdir_attr()

    def delete_key(self):
        """Delete the server's public key from remote host.

        For example::

            wrapper = RemoteWrapper(hostname, username)
            with wrapper.connect(password, public_key_filename):
                wrapper.delete_key()

        """
        if self._client is None:
            raise ValueError('Wrapper must be connected before delete_key is called')

        with open(self._public_key_filename, 'rt') as f:
            key = f.read().strip()

        self.chdir('/tmp')

        filename = 'django-remote-submission-{}'.format(uuid.uuid4)
        with self.open(filename, 'wt') as f:
            program = textwrap.dedent('''\
            sed -i.bak -e /{key}/d $HOME/.ssh/authorized_keys
            '''.format(key=cmd_quote(key.replace('/', '\/'))))

            f.write(program)

        args = [
            'bash', '/tmp/' + filename,
        ]

        self.exec_command(args, '/')


    def exec_command(self, args, workdir, timeout=None, stdout_handler=None,
                     stderr_handler=None):
        """Execute a command on the remote server.

        An example of how to use this function::

            from datetime import timedelta
            wrapper.exec_command(
                args=["ls", "-la", "."],
                workdir="/",
                timeout=timedelta(minute=5),
                stdout_handler=lambda now, output: print('stdout, now, output),
                stderr_handler=lambda now, output: print('stderr, now, output),
            )

        :param list(str) args: the command and arguments to run
        :param str workdir: the directory to run the commands from
        :param datetime.timedelta timeout: the timeout to use for the command
        :param stdout_handler: a function that accepts ``now`` and ``output``
            parameters and is called when new output appears on stdout.
        :param stderr_handler: a function that accepts ``now`` and ``output``
            parameters and is called when new output appears on stderr.

        """
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
                output = channel.recv(1024).decode('utf-8')
                if stdout_handler is not None:
                    stdout_handler(current_time, output)

            if channel.recv_stderr_ready():
                output = channel.recv_stderr(1024).decode('utf-8')
                if stderr_handler is not None:
                    stderr_handler(current_time, output)

            if channel.exit_status_ready():
                if channel.recv_ready() or channel.recv_stderr_ready():
                    continue

                if channel.recv_exit_status() == 0:
                    return True
                else:
                    return False

    def _start_client(self, password, public_key_filename):
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
    """Deploy our public key to the remote server.

    :param paramiko.client.SSHClient client: an existing Paramiko client
    :param str public_key_filename: the name of the file with the public key

    """
    with open(public_key_filename, 'rt') as f:
        key = f.read()

    client.exec_command('mkdir -p ~/.ssh/')
    client.exec_command('chmod 700 ~/.ssh/')
    client.exec_command('chmod 644 ~/.ssh/authorized_keys')

    command = textwrap.dedent('''\
    KEY={}
    if [ -z "$(grep \"$KEY\" ~/.ssh/authorized_keys )" ]; then
        printf $'%s\n' "$KEY" >> ~/.ssh/authorized_keys
        echo key added.
    fi
    '''.format(cmd_quote(key.strip('\n'))))

    stdin, stdout, stderr = client.exec_command(command)
    logger.debug(stdout.readlines())
    logger.debug(stderr.readlines())

    client.exec_command('chmod 644 ~/.ssh/authorized_keys')
