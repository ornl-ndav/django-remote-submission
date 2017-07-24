---
title: 'Django Remote Submission'
tags:
  - django
  - job submission
  - batch scheduling
authors:
 - name: Ricardo
   orcid: 0000-0002-9931-8304
   affiliation: 1
affiliations:
 - name: Oak Ridge National Laboratory
   index: 1
date: 14 February 2016
bibliography: paper.bib
---

# Summary

The Django Remote Submission (DRS) is a Django application to manage long running job submission, including starting the job, saving logs, and storing results. It is an independent project available as a standalone pypi package (https://pypi.python.org/pypi/django-remote-submission). It can be easily integrated in any Django project (https://www.djangoproject.com). The source code is available at https://github.com/ornl-ndav/django-remote-submission.

To run the jobs in background, DRS takes advantage of Celery (http://www.celeryproject.org), a powerful asynchronous job queue used for running tasks in the background, and the Redis Server (https://redis.io), an in-memory data structure store. Celery uses brokers to pass messages between a Django Project and the Celery workers. Redis is the message broker of DRS.

In addition DRS provides real time monitoring of the progress of Jobs and associated logs. Through the Django Channels projecy (https://github.com/django/channels), and the usage of Web Sockets, it is possible to asynchronously display the Job Status and the live Job output (standard output and standard error) on a web page.

# References
