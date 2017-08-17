.. django-remote-submission documentation master file, created by
   sphinx-quickstart on Wed Jan  4 13:53:46 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to django-remote-submission's documentation!
====================================================

The ``django-remote-submission`` is an asynchronous task/job queue using `Celery Distributed Task Queue <http://www.celeryproject.org/>`_ and `Redis <https://redis.io/>`_ in-memory data structure store as message broker. 

The ``django-remote-submission`` runs, remotely and asynchronously, any scripts and provides real time feedback to the client.
Altought it can be called from any python application, it is only used to its full extent when integrated in a `Django <https://www.djangoproject.com/>`_ web application.

Features
--------

* Able to connect to any server via SSH user/password or key-based authentication.

* Able to transfer and launch any script in the remote server (e.g. python or bash scripts).

* Able to capture and receive logs and write them to a database in realtime.

* Able to return any modified files from the remote server.

* Uses WebSockets to notify the Web Client of the Job status: ``initial``, ``submitted``, ``success`` or ``failure``.

* Uses WebSockets to provide Job Log (standard output and standard error) in real time to the Web Client.

User Guide
----------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   testing
   howto
   release

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
