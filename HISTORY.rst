.. :changelog:

History
-------

1.2 (2017-11-13)
+++++++++++++++++++

* Added django-filter to the REST API. Filtering in the URL is now possible. E.g.: http://localhost:8001/api/jobs/?title=Test%20Job

1.1.6 (2017-08-23)
+++++++++++++++++++

* Local Wrapper uses process.comunicate

1.1.5 (2017-08-23)
+++++++++++++++++++

* Local Wrapper does no support Live Log ever.

1.1.4 (2017-08-19)
+++++++++++++++++++

* Fixed CI tests.

1.1.3 (2017-08-19)
+++++++++++++++++++

* Local wrapper runs in all DBs without truncation.

1.1.2 (2017-08-18)
+++++++++++++++++++

* Fixed Local wrapper truncate the log.

1.1.1 (2017-08-18)
+++++++++++++++++++

* Fix issue with python 2.7

1.1.0 (2017-08-18)
+++++++++++++++++++

* Creates the remote directory if it does not exist.

1.0.1 (2017-08-18)
+++++++++++++++++++

* Updated DOC with the ``remote`` argument.

1.0.0 (2017-08-17)
+++++++++++++++++++

* All ready to be released
* Tasks have an attribute to run locally or remotelly.

0.13.0 (2017-08-17)
+++++++++++++++++++

* LocalWrapper and RemoteWrapper are in the wrapper package.

0.12.0 (2017-08-16)
+++++++++++++++++++

* Improved documentation

0.11.2 (2017-08-15)
+++++++++++++++++++

* Publication ready

0.2.0 (2016-11-17)
++++++++++++++++++

* Add django admin interface.
* Add migrations folder.
* Add log policies for submitting tasks.
* Add return value for modified files.

0.1.1 (2016-11-15)
++++++++++++++++++

* Add port number to Server model.
* Add task to submit jobs.
* Add status updates to task.
* Fix unicode error when submitting jobs.
* Fix verbose/related names for models.

0.1.0 (2016-11-08)
++++++++++++++++++

* First release on PyPI.
