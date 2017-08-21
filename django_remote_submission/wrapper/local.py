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
    
    def _is_db_sqlite(self):
        return True if 'sqlite' in settings.DATABASES['default']['ENGINE'] else False

    def exec_command(self, args, workdir, timeout=None, stdout_handler=None,
                     stderr_handler=None):
        '''
        The output of the command is written in a queue in non-sqlite DB.
        The command is faster writting output than Django writting that output
        in the DB. Some output is lost. The solution is to use Queues.
        However ir does not work for SQLite: concurrency problems. Thus the if.
        '''
        if timeout is not None:
            args = ['timeout', '{}s'.format(timeout.total_seconds())] + args

        logger.info('{!r}'.format(args))
        process = Popen(args, bufsize=1, stdout=PIPE, stderr=PIPE,
                        cwd=self.workdir, universal_newlines=True)

        rlist = [process.stdout, process.stderr]

        queue = Queue()

        def process_queue(queue):
            ''' Writes queue to the DB '''
            while True:
                print("here")
                value = queue.get()
                if value is None:
                    break
                current_time, content, func = value
                func(current_time, content)
                queue.task_done()

        t = threading.Thread(
            target=process_queue,
            args=(queue,),
        )
        t.start()

        logger.debug('Reading the process stdout / stderr')
        while process.poll() is None:
            ready, _, _ = select.select(rlist, [], [])

            current_time = now()
            if process.stdout in ready:
                stdout = process.stdout.readline()
                
                if stdout is not None and stdout != '':
                    if self._is_db_sqlite():
                        stdout_handler(current_time, stdout)
                    else:
                        queue.put([current_time, stdout, stdout_handler])

            if process.stderr in ready:
                stderr = process.stderr.readline()
                
                if stderr is not None and stderr != '':
                    if self._is_db_sqlite():
                        stderr_handler(current_time, stderr)
                    else:
                        queue.put([current_time, stderr, stderr_handler])

        queue.join()
        queue.put(None)
        t.join()
        
        logger.debug('Done reading the process stdout / stderr')

        return process.returncode == 0
