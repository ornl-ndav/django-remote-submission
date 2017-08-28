=============================
Django Remote Submission
=============================

.. image:: https://badge.fury.io/py/django-remote-submission.png
    :target: https://badge.fury.io/py/django-remote-submission

.. image:: https://travis-ci.org/ornl-ndav/django-remote-submission.png?branch=master
    :target: https://travis-ci.org/ornl-ndav/django-remote-submission

.. image:: https://codecov.io/gh/ornl-ndav/django-remote-submission/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/ornl-ndav/django-remote-submission

.. image:: https://zenodo.org/badge/DOI/10.5281/zenodo.848749.svg
   :target: https://doi.org/10.5281/zenodo.848749

.. image:: http://joss.theoj.org/papers/10.21105/joss.00366/status.svg
   :target: http://joss.theoj.org/papers/10.21105/joss.00366

A Django application to manage long running job submission, including starting the job, saving logs, and storing results.

Features
--------

* Able to connect to any server via SSH user/password or key-based authentication.

* Able to transfer and launch any script in the remote server (e.g. python or bash scripts).

* Able to capture and receive logs and write them to a database in realtime.

* Able to return any modified files from the remote server.

* Uses WebSockets to notify the Web Client of the Job status: ``initial``, ``submitted``, ``success`` or ``failure``.

* Uses WebSockets to provide Job Log (standard output and standard error) in real time to the Web Client.

Documentation
-------------

The full documentation is at https://django-remote-submission.readthedocs.org.

==========
Quickstart
==========

Install Django Remote Submission::

    pip install django-remote-submission

Then use it in a project:

.. code:: python

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

    # Using delay calls celery:
    modified_files = submit_job_to_server.delay(
        job_pk=job.pk,
        password=request.POST.get('password'),
    )

For testing, sometimes is useful to bypass the remote server and run the task in the local computer.
For this, the ``submit_job_to_server`` routine can be called with the argument ``remote=False``.
The function above would be:

.. code:: python

    modified_files = submit_job_to_server.delay(
        job_pk=job.pk,
        password=request.POST.get('password'),
        remote=False,
    )

Note that it stills use Celery. It just ignores the password passed as argument.

To avoid storing the password one can deploy the client public key in the server.

.. code:: python

    from django_remote_submission.tasks import copy_key_to_server

    copy_key_to_server(
        username=env.remote_user,
        password=env.remote_password,
        hostname=env.server_hostname,
        port=env.server_port,
        public_key_filename=None, # finds it automaticaly
    )

And it can be deleted once the session is finished:

.. code:: python

    from django_remote_submission.tasks import delete_key_from_server

    delete_key_from_server(
        username=env.remote_user,
        password=env.remote_password,
        hostname=env.server_hostname,
        port=env.server_port,
        public_key_filename=None,
    )


=================
Running the Tests
=================

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

    pytest -v tests/test_models.py
    pytest -v tests/test_models.py::test_server_string_representation

===================
Running the Example
===================

Set the ``example/.env`` file. Copy or rename ``example/.env.base`` and fill in the details of the remote machine where the ``sshd`` server is running::

    EXAMPLE_PYTHON_PATH
    EXAMPLE_PYTHON_ARGUMENTS
    EXAMPLE_SERVER_HOSTNAME
    EXAMPLE_SERVER_PORT
    EXAMPLE_REMOTE_DIRECTORY
    EXAMPLE_REMOTE_FILENAME
    EXAMPLE_REMOTE_USER
    EXAMPLE_REMOTE_PASSWORD

Set up the example's virtualenv::

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt

Launch Redis::

    redis-server

Launch Celery::

    cd example
    celery -A server.celery worker --loglevel=info

Launch Django::

    cd example
    ./manage.py makemigrations
    ./manage.py migrate
    ./manage.py loaddata fixtures/initial_data.json
    # You may want to create another user:
    # python manage.py createsuperuser
    ./manage.py runserver

Open in the browser one of the links below. The password for admin is ``admin123`` unless you prefer to use the created password::

    # For the Admin Interface
    http://localhost:8000/admin/
    # For the REST API
    http://localhost:8000/
    # To test Job creation with live status update
    http://127.0.0.1:8000/example/

=============
Web Interface
=============

The app provides two web sockets to see in real time the Job Status and the Log associated to a Job.

Those are defined in ``routing.py``::

    path=r'^/job-user/$'
    path=r'^/job-log/(?P<job_pk>[0-9]+)/$'    

The ``example`` app comes with the Live Job Status and Live Log examples. See::
    
    # Jobs
    http://127.0.0.1:8000/example/
    # Job 123 Log
    http://127.0.0.1:8000/logs/123/

Both files::

    django-remote-submission/example/templates/example_job_status.html
    django-remote-submission/example/templates/example_job_log.html

Have the client side web socket code to interact with the ``django-remote-submission`` app.
Also to include the Live information on a web app it is worth looking at the celery configuration:

``django-remote-submission/example/server/celery.py``

and the WebSockets routing:

``django-remote-submission/example/server/routing.py``

============
Useful notes
============

The Results files are stored in MEDIA. So add to your setings something similar to:

.. code:: python

	MEDIA_URL = '/media/'
	MEDIA_ROOT = '../dist/media'

To make media available in DEBUG mode, you might want to add to the main ``urls.py``:

.. code:: python

	if settings.DEBUG:
	    # Serving files uploaded by a user during development
	    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


=======
Credits
=======

Tools used in rendering this package:

*  Cookiecutter_
*  `cookiecutter-djangopackage`_

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`cookiecutter-djangopackage`: https://github.com/pydanny/cookiecutter-djangopackage

This research used resources at the High Flux Isotope Reactor and Spallation Neutron Source, a DOE Office of Science User Facility operated by the Oak Ridge National Laboratory.
