=============================
Django Remote Submission
=============================

.. image:: https://badge.fury.io/py/django-remote-submission.png
    :target: https://badge.fury.io/py/django-remote-submission

.. image:: https://travis-ci.org/ornl-ndav/django-remote-submission.png?branch=master
    :target: https://travis-ci.org/ornl-ndav/django-remote-submission

A Django application to manage long running job submission, including starting the job, saving logs, and storing results.

Documentation
-------------

The full documentation is at https://django-remote-submission.readthedocs.org.

Quickstart
----------

Install Django Remote Submission::

    pip install django-remote-submission

Then use it in a project::

    from django_remote_submission.models import Server, Job
    from django_remote_submission.tasks import submit_job_to_server

    server = Server.objects.get_or_create(
        title='My Server Title',
        hostname='example.com',
        port=22,
    )[0]
    
    interpreter = Interpreter.objects.get_or_create(
        name = 'python',
        path = '/usr/bin/python -u',
    )[0]
    
    server.interpreters.set([interpreter])

    job = Job.objects.get_or_create(
        title='My Job Title',
        program='print("hello world")',
        remote_directory='/tmp/',
        remote_filename='test.py',
        owner=request.user,
        server=server,
        interpreter=interpreter,
    )[0]

    modified_files = submit_job_to_server(
        job_pk=job.pk,
        password=request.POST.get('password'),
    )

Features
--------

* Able to connect to any server via password-authenticated SSH.

* Able to receive logs and write them to a database in realtime.

* Able to return any modified files from the remote server.

Running Tests
--------------

Does the code actually work?

::

    source <YOURVIRTUALENV>/bin/activate
    (myenv) $ pip install -r requirements_test.txt
    (myenv) $ make test

Some of the tests use a test server to check the functional aspects of the
library. Specifically, it will try to connect to the server multiple times, run
some programs, and check that their output is correct.

To run those tests as well, copy the ``.env.base`` file to ``.env`` and modify
the variables as needed. If this file has not been set up, then those tests
will be skipped, but it won't affect the success or failure of the tests.

Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
