#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-remote-submission
------------

Tests for `django-remote-submission` models module.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase

from django_remote_submission.models import Server, Job, Log, Interpreter


class ServerModelTest(TestCase):
    def setUp(self):
        self.server = Server.objects.create(
            title='1-server-title',
            hostname='1-server-hostname.invalid',
        )

    def test_string_representation(self):
        self.assertIn(str(self.server.title), str(self.server))
        self.assertIn(str(self.server.hostname), str(self.server))
        self.assertIn(str(self.server.port), str(self.server))


class JobModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username='foo')[0]

        self.server = Server.objects.create(
            title='1-server-title',
            hostname='1-server-hostname.invalid',
        )
        self.interpreter = Interpreter.objects.create(
            name = '1-interpreter-name',
            path = '1-interpreter-path',
        )
        self.server.interpreters.set([self.interpreter])

        self.job = Job.objects.create(
            title='1-job-title',
            program='1-job-program',
            owner=self.user,
            server=self.server,
            remote_directory='1-job-remote_directory',
            remote_filename='1-job-remote_filename',
            interpreter=self.interpreter,
        )

    def test_string_representation(self):
        self.assertIn(str(self.job.title), str(self.job))


class LogModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.get_or_create(username='foo')[0]

        self.server = Server.objects.create(
            title='1-server-title',
            hostname='1-server-hostname.invalid',
        )
        self.interpreter = Interpreter.objects.create(
            name = '1-interpreter-name',
            path = '1-interpreter-path',
        )
        self.server.interpreters.set([self.interpreter])

        self.job = Job.objects.create(
            title='1-job-title',
            program='1-job-program',
            owner=self.user,
            server=self.server,
            interpreter=self.interpreter,
        )

        self.log = Log.objects.create(
            content='1-log-content',
            job=self.job,
        )

    def test_string_representation(self):
        self.assertIn(str(self.log.time), str(self.log))
        self.assertIn(str(self.job), str(self.log))
