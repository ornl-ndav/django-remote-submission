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

# Practical case

The Liquids Reflectometer (LR) at the Oak Ridge National Laboratory’s Spallation Neutron Source (SNS) [@Mason2006] provides neutron reflectivity capability for an average of about 30 experiments each year. In recent years, there has been a large effort to streamline the data processing and analysis for the instrument. While much of the data reduction can be automated, data analysis remains something that needs to be done by scientists.
With this in mind, the Reflectivity Fitting Web Interface has been developed [@doucet2017]. It provides a smooth data analysis interface, capturing the process of setting up and executing fits while reducing the need for installing software or writing Python scripts.

Currently the fitting routines are written for the software package REFL1D [@Kienzle]. The management of the fitting routines is performed with the DRS. The DRS transparently submits the jobs to a cluster and provides real-time monitoring of the remote jobs and their associated logs. The user can thus track the status of the jobs and eventually inspect the associated logs. If the job was successful, DRS gathers the output data and transfer them to the webserver. Finally, the web interface provides a user friendly display and visualization of those data.

# Acknowledgments

This research used resources at the High Flux Isotope Reactor and Spallation Neutron Source, a DOE Office of Science User Facility operated by the Oak Ridge National Laboratory.

# References
