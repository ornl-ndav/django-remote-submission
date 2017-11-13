#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

version = '1.2.1'

if sys.argv[-1] == 'publish':
    try:
        import wheel
        print("Wheel version: ", wheel.__version__)
    except ImportError:
        print('Wheel library missing. Please run "pip install wheel"')
        sys.exit()
    os.system('python setup.py sdist upload')
    os.system('python setup.py bdist_wheel upload')
    sys.exit()

if sys.argv[-1] == 'tag':
    print("Tagging the version on git:")
    os.system("git tag -a %s -m 'version %s'" % (version, version))
    os.system("git push --tags")
    sys.exit()

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')

setup(
    name='django-remote-submission',
    version=version,
    description="""A Django application to manage long running job submission, including starting the job, saving logs, and storing results.""",
    long_description=readme + '\n\n' + history,
    author='T. Hobson, M. Doucet and R. M. Ferraz Leal',
    author_email='ferrazlealrm@ornl.gov',
    url='https://github.com/ornl-ndav/django-remote-submission',
    packages=[
        'django_remote_submission',
    ],
    include_package_data=True,
    install_requires=[
        # Web framework
        'django>=1.11.4',
        # Helpful utilities for creating models in Django
        'django-model-utils>=3.0.0',
        # Library to help manage REST APIs
        'djangorestframework>=3.6.3',
        # Library to manage connecting to remote hosts via SSH
        'paramiko>=2.2.1',
        # Library to help manage python 2/3 compatibility
        'six>=1.10.0',
        # Celery
        'celery>=4.1',
        # Add websocket connections to Django
        'channels>=1.1.6',
        # Filter for DRF
        'django-filter>=1.1.0',
    ],
    # install_requires=reqs,
    license="ISCL",
    zip_safe=False,
    keywords='django-remote-submission',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
