Testing the Library
====================

There are a few steps for testing the library.

1. Install dependencies
2. Modify your settings
3. Run ``make test`` or ``make test-all``


Install Dependencies
------

In order to run the tests, the dependencies need to be installed. To do this,
run these commands

.. code:: console

  $ python3 -m virtualenv venv
  $ source venv/bin/activate
  (venv)$ python3 -m pip install -r requirements_test.txt

.. _modify-settings-for-testing:

Modify Settings
------

Then copy ``.env.base`` to ``.env`` and edit the file. For example, the default
``.env.base`` file right now is:

.. include:: ../.env.base
   :code: sh

Run Tests
-------

To run the tests on your current Python version, use the target ``test``. To
run tests on multiple Python versions, use the target ``test-all``.

.. code:: console

   (venv)$ make test  # current python version
   (venv)$ make test-all  # multiple python versions
