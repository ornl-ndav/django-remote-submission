=============================
Django Remote Submission
=============================

.. image:: https://badge.fury.io/py/django-remote-submission.png
    :target: https://badge.fury.io/py/django-remote-submission

.. image:: https://travis-ci.org/ornl-ndav/django-remote-submission.png?branch=master
    :target: https://travis-ci.org/ornl-ndav/django-remote-submission

.. image:: https://codecov.io/gh/ornl-ndav/django-remote-submission/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ornl-ndav/django-remote-submission

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

    python2_interpreter = Interpreter.objects.get_or_create(
        name = 'python2',
        path = '/usr/bin/python2.7 -u',
    )[0]

    python3_interpreter = Interpreter.objects.get_or_create(
        name = 'python3',
        path = '/usr/bin/python3.5 -u',
    )[0]

    server.interpreters.set([python2_interpreter,
                             python3_interpreter])

    job = Job.objects.get_or_create(
        title='My Job Title',
        program='print("hello world")',
        remote_directory='/tmp/',
        remote_filename='test.py',
        owner=request.user,
        server=server,
        interpreter=python2_interpreter,
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

Running tests independtely, e.g.::

    python runtests.py tests.test_tasks.SubmitJobTaskTest.test_normal_usage
    python runtests.py tests.test_tasks.SubmitJobTaskTest
    python runtests.py tests.test_tasks
    python runtests.py tests.test_models

=============================
Running the Example
=============================

Launch Redis::

    redis-server

Launch Celery::

    cd example
    celery -A server.celery worker --loglevel=info

Launch Django::

    cd example
    PYTHONPATH=../ ./manage.py makemigrations
    PYTHONPATH=../ ./manage.py migrate
    PYTHONPATH=../ ./manage.py loaddata fixtures/initial_data.json
    PYTHONPATH=../ ./manage.py runserver

Open in the browser::

    http://localhost:8000/admin/
    http://localhost:8000/

=============================
Useful notes
=============================

When integrating this in django it might be usefull:

Add to settings::

	CELERY_ACCEPT_CONTENT = ['pickle']
	CELERY_EVENT_SERIALIZER = 'pickle'
	CELERY_TASK_SERIALIZER = 'pickle'  
	CELERY_RESULT_SERIALIZER = 'pickle'

if using the app ``'django_celery_results``. Otherwise Result is not serialized.

The Results files are stored in MEDIA. So add to your setings something similar to::

	MEDIA_URL = '/media/'
	MEDIA_ROOT = '../dist/media'

To make media available in DEBUG mode, you might want to add to the main ``urls.py``::

	if settings.DEBUG:
	    # Serving files uploaded by a user during development
	    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


Credits
---------

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage
