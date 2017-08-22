''' Provides a Local Wrapper to run the commands in the local machine
without the need of a sshd server.

The goal with this class is to also be able to provide a ``LocalWrapper``
which works with the local file system, so that tests can be run on
continuous integration servers.
'''

import logging
import os
import os.path
import select
import threading
from collections import namedtuple
try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from subprocess import PIPE, Popen

from django.conf import settings
from django.utils.timezone import now

from .remote import RemoteWrapper

logger = logging.getLogger(__name__)


class LocalWrapper(RemoteWrapper):
    """
    This class extends and modify the functionality of the ``RemoteWrapper``.
    It has the same functionality but does not perform any SSH connections.
    """

    def __init__(self, *args, **kwargs):
        super(LocalWrapper, self).__init__(*args, **kwargs)
        self.workdir = os.getcwd()

    def connect(self, *args, **kwargs):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        pass

    def close(self, *args, **kwargs):
        pass

    def chdir(self, remote_directory):
        self.workdir = os.path.join(self.workdir, remote_directory)

    def open(self, filename, mode):
        # create the directory + subdirectories in case they don't exist
        try:
            os.makedirs(self.workdir)
        except OSError:
            # In case the directy(ies) exist
            pass
        return open(os.path.join(self.workdir, filename), mode)

    def listdir_attr(self):
        Attr = namedtuple('Attr', ['filename', 'st_mtime'])

        results = []
        for filename in os.listdir(self.workdir):
            stat = os.stat(os.path.join(self.workdir, filename))

            results.append(Attr(
                filename=filename,
                st_mtime=stat.st_mtime,
            ))

        return results

    def exec_command(self, args, workdir, timeout=None, stdout_handler=None,
                     stderr_handler=None):
        '''
        Altouhgh Log.LIVE is possible, the Local does not support True Live Log.
        In local for large outputs, it looks like stdXXX_handle takes too long
        and the buffer of the process over runs and the log gets truncated

        '''
        if timeout is not None:
            args = ['timeout', '{}s'.format(timeout.total_seconds())] + args

        logger.info('{!r}'.format(args))
        process = Popen(args, bufsize=1, stdout=PIPE, stderr=PIPE,
                        cwd=self.workdir, universal_newlines=True)

        rlist = [process.stdout, process.stderr]

        stdout_list = []
        stderr_list = []

        logger.debug('Reading the process stdout / stderr')
        while process.poll() is None:
            ready, _, _ = select.select(rlist, [], [])

            current_time = now()
            if process.stdout in ready:
                stdout = process.stdout.readline()
                if stdout is not None and stdout != '':
                    # stdout_handler(current_time, stdout)
                    stdout_list.append((current_time, stdout))
              
            if process.stderr in ready:
                stderr = process.stderr.readline()
                if stderr is not None and stderr != '':
                    # stderr_handler(current_time, stderr)
                    stderr_list.append((current_time, stderr))
    
        # Here we store the logs in the DB
        for current_time, stdout in stdout_list:
            stdout_handler(current_time, stdout)
        for current_time, stderr in stderr_list:
            stderr_handler(current_time, stderr)

        logger.debug('Done reading the process stdout / stderr')

        return process.returncode == 0
