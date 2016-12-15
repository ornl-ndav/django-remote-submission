#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-remote-submission
------------

Tests for `django-remote-submission` tasks module.
"""
import sys
import textwrap
import datetime
import itertools

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.db.models.signals import pre_save
import environ

from django_remote_submission.models import Server, Job, Log, Interpreter
from django_remote_submission.tasks import submit_job_to_server, LogPolicy

try:
    from unittest.mock import Mock
except ImportError:
    from mock import Mock


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


class SubmitJobTaskTest(TestCase):
    def setUp(self):
        try:
            path = environ.Path(__file__) - 2
            env = environ.Env()
            environ.Env.read_env(path('.env'))

            self.server_hostname = env('TEST_SERVER_HOSTNAME')
            self.server_port = env.int('TEST_SERVER_PORT')
            self.remote_directory = env('TEST_REMOTE_DIRECTORY')
            self.remote_filename = env('TEST_REMOTE_FILENAME')
            self.remote_user = env('TEST_REMOTE_USER')
            self.remote_password = env('TEST_REMOTE_PASSWORD')
            self.interpreter_name = env('TEST_INTERPRETER_NAME')
            self.interpreter_path = env('TEST_INTERPRETER_PATH')
        except ImproperlyConfigured:
            self.skipTest('Environment variables not set')
            return

    def test_normal_usage(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import sys
        import time
        for i in range(5):
            #print("line: {}".format(i))
            print("line: {}".format(i), file=sys.stdout)
            sys.stdout.flush()
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        model_saved = Mock()
        pre_save.connect(model_saved, sender=Job)

        submit_job_to_server(job.pk, self.remote_password)

        self.assertEqual(Log.objects.count(), 5)

        min_delta = datetime.timedelta(seconds=0.05)
        max_delta = datetime.timedelta(seconds=0.3)

        for log1, log2 in pairwise(Log.objects.all()):
            delta = log2.time - log1.time
            self.assertGreaterEqual(delta, min_delta)
            self.assertLessEqual(delta, max_delta)

        self.assertEqual(model_saved.call_count, 2)
        pre_save.disconnect(model_saved, sender=Job)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)


    def test_program_failed(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )

        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )
        server.interpreters.set([interpreter])

        program = '''
        import sys
        sys.exit(1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        submit_job_to_server(job.pk, self.remote_password)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.failure)


    def test_program_log_total(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import time
        import sys
        for i in range(5):
            print("Line number: {}.".format(i), file=sys.stdout)
            sys.stdout.flush()
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        submit_job_to_server(job.pk, self.remote_password,
                             log_policy=LogPolicy.LOG_TOTAL)

        self.assertEqual(Log.objects.count(), 1)
        log = Log.objects.get()
        self.assertEqual(log.content, (
            '\n'.join('Line number: {}.'.format(x) for x in range(5))
        ))
        self.assertEqual(log.stream, 'stdout')


        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)


    def test_program_log_none(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import time
        for i in range(5):
            print(i)
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        submit_job_to_server(job.pk, self.remote_password,
                             log_policy=LogPolicy.LOG_NONE)

        self.assertEqual(Log.objects.count(), 0)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)


    def test_program_modified_files(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import time
        for i in range(5):
            with open('{}.txt'.format(i), 'w') as f:
                f.write('foo')
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        results = submit_job_to_server(job.pk, self.remote_password)

        self.assertEqual(len(results), 5)
        expected = ['0.txt', '1.txt', '2.txt', '3.txt', '4.txt']
        filenames = [x.remote_filename for x in results]
        self.assertEqual(filenames, expected)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)


    def test_program_timeout(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import sys
        import time
        for i in range(5):
            print(i, file=sys.stdout)
            sys.stdout.flush()
            time.sleep(.35)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        submit_job_to_server(job.pk, self.remote_password,
                             timeout=datetime.timedelta(seconds=1))

        self.assertEqual(Log.objects.count(), 3)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.failure)


    def test_retrieve_changed_files(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import time
        for i in range(5):
            with open('{}.txt'.format(i), 'w') as f:
                print('{}'.format(i), file=f)
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        results = submit_job_to_server(job.pk, self.remote_password)

        self.assertEqual(len(results), 5)
        expected = ['0.txt', '1.txt', '2.txt', '3.txt', '4.txt']
        filenames = [x.remote_filename for x in results]
        self.assertEqual(filenames, expected)

        for i, result in enumerate(results):
            actual = result.local_file.read().decode('utf-8')
            expected = '{}\n'.format(i)
            self.assertEqual(actual, expected)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)


    def test_retrieve_changed_files_positive_pattern(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import time
        for i in range(5):
            with open('{}.txt'.format(i), 'w') as f:
                print('{}'.format(i), file=f)
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        results = submit_job_to_server(job.pk, self.remote_password,
                                       store_results=['1.txt', '[23].txt'])

        self.assertEqual(len(results), 3)
        expected = ['1.txt', '2.txt', '3.txt']
        filenames = [x.remote_filename for x in results]
        self.assertEqual(filenames, expected)

        for i, result in enumerate(results, start=1):
            actual = result.local_file.read().decode('utf-8')
            expected = '{}\n'.format(i)
            self.assertEqual(actual, expected)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)

    def test_retrieve_changed_files_negative_pattern(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import time
        for i in range(5):
            with open('{}.txt'.format(i), 'w') as f:
                print('{}'.format(i), file=f)
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        results = submit_job_to_server(job.pk, self.remote_password,
                                       store_results=['*', '![34].txt'])

        self.assertEqual(len(results), 3)
        expected = ['0.txt', '1.txt', '2.txt']
        filenames = [x.remote_filename for x in results]
        self.assertEqual(filenames, expected)

        for i, result in enumerate(results):
            actual = result.local_file.read().decode('utf-8')
            expected = '{}\n'.format(i)
            self.assertEqual(actual, expected)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)


    def test_program_log_streams(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )

        interpreter = Interpreter.objects.create(
            name = self.interpreter_name,
            path = self.interpreter_path,
        )
        server.interpreters.set([interpreter])

        program = '''
        from __future__ import print_function
        import sys
        import time
        for i in range(5):
            print(i, file=sys.stdout)
            sys.stdout.flush()
            print(i, file=sys.stderr)
            sys.stderr.flush()
            time.sleep(0.1)
        '''

        job = Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=self.remote_directory,
            remote_filename=self.remote_filename,
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        submit_job_to_server(job.pk, self.remote_password,
                             log_policy=LogPolicy.LOG_TOTAL)

        self.assertEqual(Log.objects.count(), 2)
        self.assertEqual(Log.objects.filter(stream='stdout').count(), 1)
        self.assertEqual(Log.objects.filter(stream='stderr').count(), 1)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.success)
