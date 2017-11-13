"""Manage long running jobs using Django.

This package allows a Django web server to run jobs on remote servers and
collect their logs as well as status codes after execution. Jobs can be written
in any language as long as there is an interpreter on the server for that
language.

The main part of this package is in the :mod:`tasks` module, which has a
:func:`tasks.submit_job_to_server` function. Everything else is just setting up
the models to make this function work.

"""

__version__ = '1.2.0'

default_app_config = 'django_remote_submission.apps.DjangoRemoteSubmissionConfig'
