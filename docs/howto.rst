How To...
====================================================

This document describes how to do different things or fix different problems.

``FileNotFoundError: [Errno 2] No such file or directory: 'timeout'``
---------------------------------------------------------------------

This can show up when you run ``make test``

.. code:: console

   (venv)$ make test
   pytest
   ...
   >               raise child_exception_type(errno_num, err_msg)
   E               FileNotFoundError: [Errno 2] No such file or directory: 'timeout'

   /Users/tcf/.pyenv/versions/3.5.2/lib/python3.5/subprocess.py:1551: FileNotFoundError
   ----------------------------- Captured stdout call -----------------------------
   ['timeout', '1.0s', '/usr/bin/env', 'python3', '-u', 'foobar.py']
   ===================== 2 failed, 20 passed in 27.72 seconds =====================
   make: *** [test] Error 1

If this occurs, it's likely because the GNU ``timeout`` program does not exist
on the system that is running the test. ``timeout`` is part of the GNU
Coreutils, so make sure that is installed on the system.

To install on different systems, you would use:

.. code:: console

   $ brew install coreutils --with-default-names  # Mac OS X
   $ export PATH=/usr/local/opt/coreutils/libexec/gnubin:$PATH  # Mac OS X
   $ sudo apt-get install coreutils  # Ubuntu-like
   $ sudo yum install coreutils  # Fedora-like

All the tests were skipped
--------------------------

When you run the tests, you find that every test has an ``s`` for "skipped".

.. code:: console

   (venv)$ make test
   pytest
   ============================= test session starts ==============================
   platform darwin -- Python 3.5.2, pytest-3.0.5, py-1.4.32, pluggy-0.4.0
   rootdir: /Users/tcf/src/github.com/ornl-ndav/django-remote-submission, inifile: pytest.ini
   plugins: mock-1.5.0, django-3.1.2
   collected 22 items

   tests/test_models.py ....
   tests/test_tasks.py ssssssssssssssssss

   ===================== 4 passed, 18 skipped in 0.39 seconds =====================

When this occurs, it's because the ``.env`` file has not been configured. To
fix this, you will need to follow the instructions in
:ref:`modify-settings-for-testing`.
