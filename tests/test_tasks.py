#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-remote-submission
------------

Tests for `django-remote-submission` tasks module.
"""

import textwrap
import datetime
import itertools

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.db.models.signals import pre_save
import environ

from django_remote_submission.models import Server, Job, Log
from django_remote_submission.tasks import submit_job_to_server

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
        except ImproperlyConfigured:
            self.skipTest('Environment variables not set')
            return

    def test_normal_usage(self):
        user = get_user_model().objects.get_or_create(
            username=self.remote_user,
        )[0]

        server = Server.objects.create(
            title='1-server-title',
            hostname=self.server_hostname,
            port=self.server_port,
        )

        program = '''
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
        )

        model_saved = Mock()
        pre_save.connect(model_saved, sender=Job)

        submit_job_to_server(job.pk, server, self.remote_password)

        self.assertEqual(Log.objects.count(), 5)

        min_delta = datetime.timedelta(seconds=0.1)
        max_delta = datetime.timedelta(seconds=0.3)

        for log1, log2 in pairwise(Log.objects.all()):
            delta = log2.time - log1.time
            self.assertTrue(min_delta <= delta <= max_delta)

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
        )

        submit_job_to_server(job.pk, server, self.remote_password)

        job = Job.objects.get(pk=job.pk)
        self.assertEqual(job.status, Job.STATUS.failure)
