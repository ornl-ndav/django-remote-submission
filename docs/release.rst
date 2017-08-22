Release Process
===============

This document walks through the changes needed to fix issue #7 ("implement
``delete_key`` in the wrapper") as well as how to release the code in the
end. To make it easier to follow through with the process, I am starting on
commit ``24dcb0a``.

Create the Branch
-----------------

First we need to create a branch off of master that we can implement our
changes in. From the command line, this is:

.. code:: console

   $ git checkout master  # make sure we start on master branch
   $ git checkout -b add-delete-key-functionality

Add Test
--------

In this case, I already have a test that does most of the work, I just need to
factor out a part of the test to use a new utility function and make a new one
that works with the wrapper directly instead of the job interface. From the
issue, we want to be able to do:

.. code:: python

   wrapper = RemoteWrapper(hostname=server.hostname, username=username)
   with wrapper.connect(password=None, public_key_filename=public_key_path):
       wrapper.delete_key()

The test that I ended up writing is:

.. code:: python


   @pytest.mark.django_db
   def test_delete_key(env):
       from django_remote_submission.remote import RemoteWrapper

       if pytest.config.getoption('--ci'):
           pytest.skip('does not work in CI environments')

       wrapper = RemoteWrapper(
           hostname=env.server_hostname,
           username=env.remote_user,
           port=env.server_port,
       )

       with wrapper.connect(password=env.remote_password):
           wrapper.delete_key()

       with pytest.raises(ValueError, message='needs password'):
           with wrapper.connect(password=None):
               pass

Ensure that Test Currently Fails
--------------------------------

Once we have our test, we want to make sure it fails. We can do this in two
ways, either by running the entire test suite or by just running the specific
test. I put the earlier test in the ``test/test_tasks.py`` file, so if your
test belongs somewhere else, then make sure to change the name appropriately.

.. code:: console

   $ source venv/bin/activate
   (venv)$ make test  # Run all the tests
   (venv)$ pytest tests/test_tasks.py::test_delete_key  # Run one test

Add Necessary Code to Make Test Pass
------------------------------------

Now we just need to implement the functionality to get the test(s) to pass. In
this case, I had to actually change a few things, but the main part was just
implementing the ``delete_key`` method.

Test Multiple Python Versions
-----------------------------

Once it works on the main Python version we're using, we also need to make sure
it works with other versions by running:

.. code:: console

   $ source venv/bin/activate
   (venv)$ make test-all

Commit Changes
--------------

Now we need to commit our changes and push to our feature branch so we can get
Travis to run our tests. This may need several iterations to get working in
case there are weird edge cases. Usually for parts of this library that pertain
to actually connecting to a remote host, we'll need to have the test be skipped
if it's running on continuous integration hosts.

.. code:: python

   if pytest.config.getoption('--ci'):
       pytest.skip('does not work in CI environments')

Make Documentation Changes
--------------------------

Some changes will need changes to the documentation to be made, whether that's
adding docstrngs to the implemented methods or adding new pages to the
documentation index. Once the changes are made, you should rebuild the
documentationt o ensure that it is still working, and taking care to keep track
of any warnings (such as "this page has not been included anywhere").

.. code:: console

   $ make docs

Commit Changes
--------------

Again, commit and push the latest changes and ensure it's still working in
Travis.

Make Pull Request and Merge
---------------------------

Finally, we just need to actually make the pull request. Go to GitHub, select
the feature branch, and select "Compare and Pull Request". In the body of the
message, make sure to reference any issues that it fixes. Travis and a few
other integrations will add a comment detailing whether the pull request will
successfully merge or not, so pay attention to those warnings or errors.

Once everything passes, then merge the pull request and close the relevant
issues.

Update HISTORY.rst and bumpversion
----------------------------------

Now that the feature branch has been merged into master, we need to switch back
to the master branch, update ``HISTORY.rst`` and bump the version.

.. code:: console

   $ git checkout master
   $ git pull origin master
   $ source venv/bin/activate
   (venv)$ python -m pip install -r requirements_dev.txt
   (venv)$ bumpversion patch  # or minor or major
   $ git push origin master
   $ git push origin --tags

Release to PyPI
---------------

The last step is to actually release to PyPI. To do this, we first need to make
sure we have a ``~/.pypirc`` file:

.. code:: ini

   [distutils]
   index-servers =
       pypi

   [pypi]
   repository: https://www.python.org/pypi
   username: YOUR_USERNAME
   password: YOUR_PASSWORD

And then we just need to make sure we're on the master branch (now that we've
merged the feature branch).

.. code:: console

   (venv)$ make release
