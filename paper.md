---
title: 'Django Remote Submission'
tags:
  - django
  - job submission
  - batch scheduling
authors:
- name: Tanner C. Hobson
   orcid: 0000-0002-6269-7881
   affiliation: 1
- name: Mathieu Doucet
   orcid: 0000-0002-5560-6478
   affiliation: 1
 - name: Ricardo M. Ferraz Leal
   orcid: 0000-0002-9931-8304
   affiliation: 1
affiliations:
 - name: Oak Ridge National Laboratory
   index: 1
date: 24 July 2017
bibliography: paper.bib
---

# Summary

The Django Remote Submission (DRS) is a Django [@Django] application to manage long running job submission, including starting the job, saving logs, and storing results. It is an independent project available as a standalone pypi package [@PyPi]. It can be easily integrated in any Django project. The source code is freely available as a GitHub repository [@django-remote-submission].

To run the jobs in background, DRS takes advantage of Celery [@Celery], a powerful asynchronous job queue used for running tasks in the background, and the Redis Server [@Redis], an in-memory data structure store. Celery uses brokers to pass messages between a Django Project and the Celery workers. Redis is the message broker of DRS.

In addition DRS provides real time monitoring of the progress of Jobs and associated logs. Through the Django Channels project [@Channels], and the usage of Web Sockets, it is possible to asynchronously display the Job Status and the live Job output (standard output and standard error) on a web page.

# References
