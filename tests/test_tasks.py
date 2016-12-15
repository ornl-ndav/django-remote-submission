#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-remote-submission
------------

Tests for `django-remote-submission` tasks module.
"""

import collections
import pytest
import textwrap

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    import itertools

    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


EnvBase = collections.namedtuple('Env', [
    'server_hostname', 'server_port', 'remote_directory', 'remote_filename',
    'remote_user', 'remote_password', 'interpreter_name',
    'interpreter_path',
])


class Env(EnvBase):
    def __repr__(self):
        return super(Env, self).__repr__().replace(
            'remote_password={!r}'.format(self.remote_password),
            'remote_password={!r}'.format('******'),
        )


@pytest.fixture
def env():
    import environ

    path = environ.Path(__file__) - 2
    env = environ.Env()
    environ.Env.read_env(path('.env'))

    try:
        return Env(
            server_hostname=env('TEST_SERVER_HOSTNAME'),
            server_port=env.int('TEST_SERVER_PORT'),
            remote_directory=env('TEST_REMOTE_DIRECTORY'),
            remote_filename=env('TEST_REMOTE_FILENAME'),
            remote_user=env('TEST_REMOTE_USER'),
            remote_password=env('TEST_REMOTE_PASSWORD'),
            interpreter_name=env('TEST_INTERPRETER_NAME'),
            interpreter_path=env('TEST_INTERPRETER_PATH'),
        )
    except Exception as e:
        pytest.skip('Environment variables not set: {!r}'.format(e))


@pytest.fixture
def user(env):
    from django.contrib.auth import get_user_model

    return get_user_model().objects.create(
        username=env.remote_user,
    )


@pytest.fixture
def interpreter(env):
    from django_remote_submission.models import Interpreter

    return Interpreter.objects.create(
        name=env.interpreter_name,
        path=env.interpreter_path,
    )


@pytest.fixture
def server(env, interpreter):
    from django_remote_submission.models import Server

    server = Server.objects.create(
        title='1-server-title',
        hostname=env.server_hostname,
    )
    server.interpreters.set([interpreter])

    return server


@pytest.fixture
def job(request, env, server, user, interpreter):
    from django_remote_submission.models import Job

    marker = request.node.get_marker('job_program')
    if not marker:
        pytest.fail('No marker "job_program" specified')

    return Job.objects.create(
        title='1-job-title',
        program=textwrap.dedent(marker.args[0]),
        remote_directory=env.remote_directory,
        remote_filename=env.remote_filename,
        server=server,
        owner=user,
        interpreter=interpreter,
    )


@pytest.fixture
def job_model_saved(mocker):
    from django.db.models.signals import pre_save
    from django_remote_submission.models import Job

    mock = mocker.Mock()
    pre_save.connect(mock, sender=Job)

    yield mock

    pre_save.disconnect(mock, sender=Job)


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
for i in range(5):
    print("line: {}".format(i))
    time.sleep(0.1)
''')
def test_submit_job_normal_usage(env, job, job_model_saved):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server
    import datetime

    submit_job_to_server(job.pk, env.remote_password)

    assert Log.objects.count() == 5

    min_delta = datetime.timedelta(seconds=0.05)
    max_delta = datetime.timedelta(seconds=0.3)
    for log1, log2 in pairwise(Log.objects.all()):
        delta = log2.time - log1.time
        assert min_delta <= delta <= max_delta

    for i, log in enumerate(Log.objects.all()):
        assert log.content == 'line: {}'.format(i)

    assert job_model_saved.call_count == 2

    job = Job.objects.get(pk=job.pk)
    assert job.status == Job.STATUS.success
