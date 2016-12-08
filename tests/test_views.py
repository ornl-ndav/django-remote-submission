#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-remote-submission
------------

Tests for `django-remote-submission` views module.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from django_remote_submission.models import Server, Job, Log, Interpreter


class ServerViewTest(APITestCase):
    def test_server_listing_with_no_servers(self):
        url = reverse('server-list')
        data = None
        expected = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected)

    def test_server_listing_with_one_server(self):
        server = Server.objects.create(
            title='1-server-title',
            hostname='1-server-hostname.invalid',
        )
        server.save()

        url = reverse('server-list')
        data = None
        expected = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': server.id,
                    'title': server.title,
                    'hostname': server.hostname,
                },
            ],
        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected)


class JobViewTest(APITestCase):
    def test_job_listing_with_no_jobs(self):
        url = reverse('job-list')
        data = None
        expected = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected)

    def test_job_listing_with_one_job(self):
        server = Server.objects.create(
            title='1-server-title',
            hostname='1-server-hostname.invalid',
        )
        interpreter = Interpreter.objects.create(
            name = '1-interpreter-name',
            path = '1-interpreter-path',
        )
        server.interpreters.set([interpreter])

        user = get_user_model().objects.create(
            username='1-user-username',
        )
        user.save()

        job = Job.objects.create(
            title='1-job-title',
            program='1-job-program',
            owner=user,
            server=server,
            interpreter=interpreter,
        )

        url = reverse('job-list')
        data = None
        expected = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': job.id,
                    'title': job.title,
                    'program': job.program,
                    'status': job.status,
                    'owner': user.id,
                    'server': server.id,
                },
            ],
        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected)


class LogViewTest(APITestCase):
    def test_log_listing_with_no_logs(self):
        url = reverse('log-list')
        data = None
        expected = {
            'count': 0,
            'next': None,
            'previous': None,
            'results': [],
        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected)

    def test_log_listing_with_one_log(self):
        server = Server.objects.create(
            title='1-server-title',
            hostname='1-server-hostname.invalid',
        )
        interpreter = Interpreter.objects.create(
            name = '1-interpreter-name',
            path = '1-interpreter-path',
        )
        server.interpreters.set([interpreter])

        user = get_user_model().objects.create(
            username='1-user-username',
        )
        user.save()

        job = Job.objects.create(
            title='1-job-title',
            program='1-job-program',
            owner=user,
            server=server,
            interpreter=interpreter,
        )
        job.save()

        log = Log.objects.create(
            content='1-log-content',
            job=job,
        )
        log.save()

        url = reverse('log-list')
        data = None
        expected = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [
                {
                    'id': log.id,
                    'time': log.time.isoformat()[:-6] + 'Z',
                    'content': log.content,
                    'stream': 'stdout',
                    'job': job.id,
                },
            ],
        }
        response = self.client.get(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.data, expected)
