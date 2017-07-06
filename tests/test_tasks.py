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
import os
import logging
import sys
from django_remote_submission.remote import RemoteWrapper


logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    import itertools

    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)


skip_if_ci = pytest.mark.skipif(
    pytest.config.getoption('--ci'),
    reason='some things do not work on ci',
)


EnvBase = collections.namedtuple('Env', [
    'server_hostname', 'server_port', 'remote_directory', 'remote_filename',
    'remote_user', 'remote_password', 'python_path', 'python_arguments',
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
            python_path=env('TEST_PYTHON_PATH'),
            python_arguments=env.list('TEST_PYTHON_ARGUMENTS'),
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
        name='Python',
        path=env.python_path,
        arguments=env.python_arguments,
    )


@pytest.fixture
def interpreter_gen(env):
    from django_remote_submission.models import Interpreter

    def gen(name, path, arguments):
        return Interpreter.objects.create(
            name=name,
            path=path,
            arguments=arguments,
        )

    return gen


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
def job_gen(request, env, server, user):
    from django_remote_submission.models import Job

    def gen(program, interpreter):
        return Job.objects.create(
            title='1-job-title',
            program=textwrap.dedent(program),
            remote_directory=env.remote_directory,
            remote_filename=env.remote_filename,
            server=server,
            owner=user,
            interpreter=interpreter,
        )

    return gen


@pytest.fixture
def job_model_saved(mocker):
    from django.db.models.signals import pre_save
    from django_remote_submission.models import Job

    mock = mocker.Mock()
    pre_save.connect(mock, sender=Job)

    yield mock

    pre_save.disconnect(mock, sender=Job)


@pytest.fixture(params=[True, False])
def wrapper_cls(request):
    from django_remote_submission.remote import RemoteWrapper
    import os
    import os.path
    import select
    from subprocess import Popen, PIPE
    from collections import namedtuple
    from django.utils.timezone import now

    class LocalWrapper(RemoteWrapper):
        def __init__(self, *args, **kwargs):
            super(LocalWrapper, self).__init__(*args, **kwargs)
            self.workdir = os.getcwd()
            print(dir(self))

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
            if timeout is not None:
                args = ['timeout', '{}s'.format(timeout.total_seconds())] + args

            print('{!r}'.format(args))
            process = Popen(args, bufsize=1, stdout=PIPE, stderr=PIPE,
                            cwd=self.workdir, universal_newlines=True)

            rlist = [process.stdout, process.stderr]

            print('before loop')
            while process.poll() is None:
                ready, _, _ = select.select(rlist, [], [])

                current_time = now()
                if process.stdout in ready:
                    stdout = process.stdout.readline()

                    if stdout != '':
                        stdout_handler(current_time, stdout)

                if process.stderr in ready:
                    stderr = process.stderr.readline()

                    if stderr != '':
                        stderr_handler(current_time, stderr)

            print('after loop')

            return process.returncode == 0

    if request.param:
        # return RemoteWrapper
        return LocalWrapper
    elif pytest.config.getoption('--ci'):
        pytest.skip('running on continuous integration')
    else:
        return RemoteWrapper


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
for i in range(5):
    print("line: {}".format(i))
    time.sleep(0.1)
''')
def test_submit_job_normal_usage(env, job, job_model_saved, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server
    import datetime

    submit_job_to_server(job.pk, env.remote_password, wrapper_cls=wrapper_cls)

    job = Job.objects.get(pk=job.pk)
    assert job.status == Job.STATUS.success

    assert Log.objects.count() == 5

    min_delta = datetime.timedelta(seconds=0.05)
    max_delta = datetime.timedelta(seconds=0.3)
    for log1, log2 in pairwise(Log.objects.all()):
        delta = log2.time - log1.time
        assert min_delta <= delta <= max_delta

    for i, log in enumerate(Log.objects.all()):
        assert log.content == 'line: {}\n'.format(i)

    assert job_model_saved.call_count == 2


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    print("line: {}".format(i), file=sys.stdout if i % 2 == 0 else sys.stderr)
    time.sleep(0.1)
''')
def test_submit_job_multiple_streams(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server
    import datetime

    submit_job_to_server(job.pk, env.remote_password, wrapper_cls=wrapper_cls)

    assert Log.objects.count() == 5

    min_delta = datetime.timedelta(seconds=0.05)
    max_delta = datetime.timedelta(seconds=0.3)
    for log1, log2 in pairwise(Log.objects.all()):
        delta = log2.time - log1.time
        assert min_delta <= delta <= max_delta

    for i, log in enumerate(Log.objects.all()):
        assert log.content == 'line: {}\n'.format(i)
        if i % 2 == 0:
            assert log.stream == 'stdout'
        else:
            assert log.stream == 'stderr'


@pytest.mark.django_db
@pytest.mark.job_program('''\
import sys
sys.exit(1)
''')
def test_submit_job_failure(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server

    submit_job_to_server(job.pk, env.remote_password, wrapper_cls=wrapper_cls)

    job = Job.objects.get(pk=job.pk)
    assert job.status == Job.STATUS.failure


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    print('line: {}'.format(i), file=sys.stdout)
    time.sleep(0.1)
''')
def test_submit_job_log_policy_log_total(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy

    submit_job_to_server(job.pk, env.remote_password, wrapper_cls=wrapper_cls,
                         log_policy=LogPolicy.LOG_TOTAL)

    assert Log.objects.count() == 1
    log = Log.objects.get()
    assert log.content == ''.join('line: {}\n'.format(i) for i in range(5))
    assert log.stream == 'stdout'


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    print('line: {}'.format(i), file=sys.stdout)
    time.sleep(0.1)
''')
def test_submit_job_log_policy_log_none(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy

    submit_job_to_server(job.pk, env.remote_password, wrapper_cls=wrapper_cls,
                         log_policy=LogPolicy.LOG_NONE)

    assert Log.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    print('line: {}'.format(i))
    time.sleep(0.35)
''')
def test_submit_job_timeout(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy
    import datetime

    submit_job_to_server(job.pk, env.remote_password,
                         wrapper_cls=wrapper_cls,
                         timeout=datetime.timedelta(seconds=1))

    assert Log.objects.count() == 3

    job = Job.objects.get(pk=job.pk)
    assert job.status == Job.STATUS.failure


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    with open('{}.txt'.format(i), 'w') as f:
        print('line: {}'.format(i), file=f)
    time.sleep(0.1)
''')
def test_submit_job_modified_files(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log, Result
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy
    import re

    results = submit_job_to_server(job.pk, env.remote_password,
                                   wrapper_cls=wrapper_cls)

    assert len(results) == 5
    assert sorted(results.keys()) == \
        ['0.txt', '1.txt', '2.txt', '3.txt', '4.txt']

    for (result_fname, result_pk) in results.items():
        result = Result.objects.get(pk=result_pk)
        i = int(re.match(r'^([0-9])\.txt', result_fname).group(1))

        assert result.local_file.read().decode('utf-8') == \
            'line: {}\n'.format(i)

    matcher = re.compile(
        r'results/{}/[0-4].txt'.format(job.uuid)
    )

    assert matcher.match(result.local_file.name) is not None


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    with open('{}.txt'.format(i), 'w') as f:
        print('line: {}'.format(i), file=f)
    time.sleep(0.1)
''')
def test_submit_job_modified_files_positive_pattern(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log, Result
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy
    import re

    results = submit_job_to_server(job.pk, env.remote_password,
                                   wrapper_cls=wrapper_cls,
                                   store_results=['0.txt', '[12].txt'])

    assert len(results) == 3
    assert sorted(results.keys()) == \
        ['0.txt', '1.txt', '2.txt']

    for (result_fname, result_pk) in results.items():
        result = Result.objects.get(pk=result_pk)
        i = int(re.match(r'^([0-9])\.txt', result_fname).group(1))

        assert result.local_file.read().decode('utf-8') == \
            'line: {}\n'.format(i)


@pytest.mark.django_db
@pytest.mark.job_program('''\
from __future__ import print_function
import time
import sys
for i in range(5):
    with open('{}.txt'.format(i), 'w') as f:
        print('line: {}'.format(i), file=f)
    time.sleep(0.1)
''')
def test_submit_job_modified_files_negative_pattern(env, job, wrapper_cls):
    from django_remote_submission.models import Job, Log, Result
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy
    import re

    results = submit_job_to_server(job.pk, env.remote_password,
                                   wrapper_cls=wrapper_cls,
                                   store_results=['*', '![34].txt'])

    assert len(results) == 3
    assert sorted(results.keys()) == \
        ['0.txt', '1.txt', '2.txt']

    for (result_fname, result_pk) in results.items():
        result = Result.objects.get(pk=result_pk)
        i = int(re.match(r'^([0-9])\.txt', result_fname).group(1))

        assert result.local_file.read().decode('utf-8') == \
            'line: {}\n'.format(i)


@pytest.mark.django_db
def test_submit_job_deploy_key(env, job_gen, interpreter_gen, wrapper_cls):
    from django_remote_submission.models import Job, Log
    from django_remote_submission.tasks import submit_job_to_server, LogPolicy
    import os.path
    import time

    try:
        from shlex import quote as cmd_quote
    except ImportError:
        from pipes import quote as cmd_quote

    sh = interpreter_gen(
        name='sh',
        path='/usr/bin/env',
        arguments=['sh'],
    )

    python = interpreter_gen(
        name='Python',
        path='/usr/bin/env',
        arguments=['python', '-u'],
    )

    with open(os.path.expanduser('~/.ssh/id_rsa.pub'), 'rt') as f:
        key = f.read().strip()

    remove_existing_key_job = job_gen(
        program='''\
        sed -i.bak -e /{key}/d ~/.ssh/authorized_keys
        '''.format(key=cmd_quote(key.replace('/', '\/'))),
        interpreter=sh,
    )

    submit_job_to_server(remove_existing_key_job.pk, env.remote_password,
                         wrapper_cls=wrapper_cls)

    add_key_job = job_gen(
        program='''\
        true
        ''',
        interpreter=sh,
    )

    submit_job_to_server(add_key_job.pk, env.remote_password,
                         wrapper_cls=wrapper_cls)


@pytest.mark.skipif(
    pytest.config.getoption('--ci'),
    reason='Does not work on ci',
)
@pytest.mark.django_db
def test_delete_key_old_way(env):
    from django_remote_submission.remote import RemoteWrapper

    # if pytest.config.getoption('--ci'):
    #     pytest.skip('does not work in CI environments')

    wrapper = RemoteWrapper(
        hostname=env.server_hostname,
        username=env.remote_user,
        port=env.server_port,
    )

    public_key_filename = os.path.expanduser('~/.ssh/id_rsa.pub')

    # Connect with password drop the key
    with wrapper.connect(env.remote_password, public_key_filename):
        wrapper.deploy_key_if_it_does_not_exist()

    # Connect without password
    with wrapper.connect():
        pass

    # delete the they
    with wrapper.connect(env.remote_password):
        wrapper.delete_key()

@pytest.mark.skipif(
    pytest.config.getoption('--ci'),
    reason='Does not work on ci',
)
@pytest.mark.django_db
def test_deploy_and_delete_key(env, wrapper_cls=RemoteWrapper):
    '''
    This is the new way of deploying and deleting the private key
    '''
    from django_remote_submission.tasks import (
        copy_key_to_server,
        delete_key_from_server
    )

    copy_key_to_server(
        username=env.remote_user,
        password=env.remote_password,
        hostname=env.server_hostname,
        port=env.server_port,
        public_key_filename=None,
        wrapper_cls=wrapper_cls,
    )
    # This wrapper is just for testing
    # Note that no password is passed!
    wrapper = wrapper_cls(
        hostname=env.server_hostname,
        username=env.remote_user,
        port=env.server_port,
    )

    # Connect without password
    with wrapper.connect():
        pass
    
    delete_key_from_server(
        username=env.remote_user,
        password=env.remote_password,
        hostname=env.server_hostname,
        port=env.server_port,
        public_key_filename=None,
        wrapper_cls=wrapper_cls,
    )

    with pytest.raises(ValueError, message="incorrect public key"):
        # Connect without password fails!
        with wrapper.connect():
            pass

