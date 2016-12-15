#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-remote-submission
------------

Tests for `django-remote-submission` models module.
"""

import pytest

@pytest.fixture
def server():
    from django_remote_submission.models import Server

    return Server.objects.create(
        title='1-server-title',
        hostname='1-server-hostname.invalid',
    )

@pytest.fixture
def user():
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create(
        username='1-user-username',
    )


@pytest.fixture
def interpreter():
    from django_remote_submission.models import Interpreter

    return Interpreter.objects.create(
        name='1-interpreter-name',
        path='1-interpreter-path',
    )


@pytest.fixture
def job(server, user, interpreter):
    from django_remote_submission.models import Job

    return Job.objects.create(
        title='1-job-title',
        program='1-job-program',
        remote_directory='1-job-remote_directory',
        remote_filename='1-job-remote_filename',
        server=server,
        owner=user,
        interpreter=interpreter,
    )


@pytest.fixture
def log(job):
    from django_remote_submission.models import Log

    return Log.objects.create(
        content='1-log-content',
        job=job,
    )


@pytest.fixture
def result(job):
    from django_remote_submission.models import Result

    return Result.objects.create(
        remote_filename='1-result-remote_filename',
        job=job,
    )


@pytest.mark.django_db
def test_server_string_representation(server):
    assert str(server.title) in str(server)
    assert str(server.hostname) in str(server)
    assert str(server.port) in str(server)


@pytest.mark.django_db
def test_job_string_representation(job):
    assert str(job.title) in str(job)


@pytest.mark.django_db
def test_log_string_representation(log):
    assert str(log.time) in str(log)
    assert str(log.job) in str(log)


@pytest.mark.django_db
def test_result_string_representation(result):
    assert str(result.remote_filename) in str(result)
    assert str(result.job) in str(result)
