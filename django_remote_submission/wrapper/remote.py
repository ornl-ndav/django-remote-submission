"""Provides a wrapper around Paramiko to simplify the API.

This module is meant to be a general wrapper so other wrappers can
also be created to run tests in continuous integration services where SSH is
not available.

"""

from __future__ import absolute_import, print_function, unicode_literals

import datetime
import logging
import os
import textwrap
import uuid

import six
from django.utils.timezone import now
from paramiko import AuthenticationException, BadHostKeyException
from paramiko.client import AutoAddPolicy, SSHClient

try:
    from shlex import quote as cmd_quote
except ImportError:
    from pipes import quote as cmd_quote


logger = logging.getLogger(__name__)


class RemoteWrapper(object):
    """
    Wrapper around Paramiko which simplifies the remote connection API.
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

        self._public_key_filename = None
        """The Public key passed as parameter"""

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
        # DO NOT FIND THE PUBLIC KEY!
        # if public_key_filename is None:
        #     public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')

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

    def _mkdir_p(self, remote_directory):
        """Change to this directory, recursively making new folders if needed.
        Returns True if any folders were created.

        Thanks: https://stackoverflow.com/questions/14819681/upload-files-\
        using-sftp-in-python-but-create-directories-if-path-doesnt-exist
        
        :param str remote_directory: the directory to create
        """
        if remote_directory == '/':
            # absolute path so change directory to root
            self._sftp.chdir('/')
            return
        if remote_directory == '':
            # top-level relative directory must exist
            return
        try:
            self._sftp.chdir(remote_directory)  # sub-directory exists
        except IOError:
            dirname, basename = os.path.split(remote_directory.rstrip('/'))
            self._mkdir_p(dirname)  # make parent directories
            self._sftp.mkdir(basename)  # sub-directory missing, so created it
            self._sftp.chdir(basename)
            return True

    def chdir(self, remote_directory):
        """Change directories to the remote directory.

        :param str remote_directory: the directory to change to

        """
        self._mkdir_p(remote_directory)
        # self._sftp.chdir(remote_directory)

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
        logger.info('exec_command(command={!r})'.format(command))

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
        '''
        Try to loginf first with public_key_filename then with password
        '''
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())

        username = self.username
        server_hostname = self.hostname
        server_port = self.port

        if password is not None:
            try:
                logger.info("Connecting user %s to %s with password.",
                            username, server_hostname)
                client.connect(
                    server_hostname,
                    port=server_port,
                    username=username,
                    password=password,
                    timeout=5,
                    
                )
            except AuthenticationException as e:
                logger.error("Authenctication error! Wrong password...")
                six.raise_from(ValueError('incorrect password'), e)
        else:
            logger.debug("Trying to connect with the public key")
            if public_key_filename is None:
                public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')
            if (public_key_filename is not None and 
                    os.path.exists(public_key_filename)):
                try:
                    logger.info("Connecting to %s with public key.",
                                server_hostname)
                    client.connect(
                        server_hostname,
                        port=server_port,
                        username=username,
                        key_filename=public_key_filename,
                    )
                except AuthenticationException as e:
                    logger.error("Problems connecting with the public key...")
                    six.raise_from(ValueError('incorrect public key'), e)
            else:
                logger.error("You need to provide either a valid Public Key \
                    or Password!")
                raise ValueError('To connect to the server you need \
                    either a password or your public key!')

        return client

    def _make_command(self, args, timeout):
        command = ' '.join(cmd_quote(arg) for arg in args)

        if timeout is not None:
            command = 'timeout {}s {}'.format(timeout.total_seconds(), command)
        return command

    def deploy_key_if_it_does_not_exist(self):
        """Deploy our public key to the remote server.

        :param paramiko.client.SSHClient client: an existing Paramiko client
        :param str public_key_filename: the name of the file with the public key

        This can be called as:
            key = os.path.expanduser('~/.ssh/id_rsa.pub')
            wrapper = RemoteWrapper(hostname=server.hostname, username=username)
            wrapper.connect(password)
            wrapper.deploy_key_if_it_does_not_exist()
            wrapper.close()

        """

        if self._public_key_filename is None:
            self._public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')
        if self._client is None:
            raise ValueError('Wrapper must be connected before deploy_key is called')

        with open(self._public_key_filename, 'rt') as f:
            key = f.read().strip()

        self._client.exec_command('mkdir -p ~/.ssh/')
        self._client.exec_command('chmod 700 ~/.ssh/')
        self._client.exec_command('chmod 644 ~/.ssh/authorized_keys')

        command = textwrap.dedent('''\
        KEY={}
        if [ -z "$(grep \"$KEY\" ~/.ssh/authorized_keys )" ]; then
            printf $'%s\n' "$KEY" >> ~/.ssh/authorized_keys
            echo key added.
        fi
        '''.format(cmd_quote(key.strip('\n'))))

        stdin, stdout, stderr = self._client.exec_command(command)
        logger.debug(stdout.readlines())
        logger.debug(stderr.readlines())

        self._client.exec_command('chmod 644 ~/.ssh/authorized_keys')

    def delete_key(self):
        """Delete the server's public key from remote host.

        For example::

            wrapper = RemoteWrapper(hostname, username)
            with wrapper.connect(password, public_key_filename):
                wrapper.delete_key()

        """
        if self._public_key_filename is None:
            self._public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')
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
