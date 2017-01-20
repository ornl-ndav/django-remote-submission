"""Provide the Django models for interfacing with the job submission tasks.

.. code::

    +----------------+            +---------------+
    | "Server"       | +--+------>| "Interpreter" |
    +----------------+ |  |       +---------------+
    | "interpreters" +-+  |
    | "job_set"      +--+ |       +---------------+
    +----------------+  | | +---->| "Result"      |
                        | | |     +---------------+
    +----------------+  | | |
    | "Job"          |<-+ | |     +---------------+
    +----------------+    | | +-->| "Log"         |
    | "interpreter"  +----+ | |   +---------------+
    | "results"      +------+ |
    | "logs"         +--------+   +---------------+
    | "owner"        +----------->| "User"        |
    +----------------+            +---------------+

"""
# -*- coding: utf-8 -*-
import ast
import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError

from model_utils import Choices
from model_utils.fields import StatusField, AutoCreatedField
from model_utils.models import TimeStampedModel


# Thanks http://stackoverflow.com/a/7394475
class ListField(models.TextField):  # noqa: D101
    description = "Stores a python list"

    def __init__(self, *args, **kwargs):  # noqa: D102
        super(ListField, self).__init__(*args, **kwargs)

    def to_python(self, value):  # noqa: D102
        if not value:
            value = []

        if isinstance(value, list):
            return value

        return ast.literal_eval(value)

    def from_db_value(self, value, expression, connection, context):  # noqa: D102
        return self.to_python(value)

    def get_prep_value(self, value):  # noqa: D102
        if value is None:
            return value

        return str(value)

    def value_to_string(self, obj):  # noqa: D102
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)


@python_2_unicode_compatible
class Interpreter(TimeStampedModel):
    """Encapsulates the executable and required arguments for each interpreter.

    >>> from django_remote_submission.models import Interpreter
    >>> python3 = Interpreter(
    ...     name='Python 3',
    ...     path='/usr/bin/python3',
    ...     arguments=['-u'],
    ... )
    >>> python3
    <Interpreter: Python 3 (/usr/bin/python3)>

    """

    name = models.CharField(
        _('Interpreter Name'),
        help_text=_('The human-readable name of the interpreter'),
        max_length=100,
    )

    path = models.CharField(
        _('Command Full Path'),
        help_text=_('The full path of the interpreter path.'),
        max_length=256,
    )

    arguments = ListField(
        _('Command Arguments'),
        help_text=_('The arguments used when running the interpreter'),
        max_length=256,
    )

    class Meta:  # noqa: D101
        verbose_name = _('interpreter')
        verbose_name_plural = _('interpreters')

    def __str__(self):
        """Convert model to string, e.g. ``"Python 3 (/usr/bin/python3)"``."""
        return '{self.name} ({self.path})'.format(self=self)


@python_2_unicode_compatible
class Server(TimeStampedModel):
    """Encapsulates the remote server identifiers.

    .. testsetup::

       from django_remote_submission.models import Interpreter
       python3 = Interpreter(name='Python 3', path='/bin/python3', arguments=['-u'])

    >>> from django_remote_submission.models import Server
    >>> server = Server(
    ...     title='Remote',
    ...     hostname='foo.invalid',
    ...     port=22,
    ... )
    >>> server.interpreters.set([python3])  # doctest: +SKIP
    >>> server
    <Server: Remote <foo.invalid:22>>

    """

    title = models.CharField(
        _('Server Name'),
        help_text=_('The human-readable name of the server'),
        max_length=100,
    )

    hostname = models.CharField(
        _('Server Hostname'),
        help_text=_('The hostname used to connect to the server'),
        max_length=100,
    )

    port = models.IntegerField(
        _('Server Port'),
        help_text=_('The port to connect to for SSH (usually 22)'),
        default=22,
    )

    interpreters = models.ManyToManyField(
        Interpreter,
        verbose_name=_("List of interpreters available for this Server")
    )

    class Meta:  # noqa: D101
        verbose_name = _('server')
        verbose_name_plural = _('servers')

    def __str__(self):
        """Convert model to string, e.g. ``"Remote <foo.invalid:22>"``."""
        return '{self.title} <{self.hostname}:{self.port}>'.format(self=self)


@python_2_unicode_compatible
class Job(TimeStampedModel):
    """Encapsulates the information about a particular job.

    .. testsetup::

       from django_remote_submission.models import Server, Interpreter
       from django.contrib.auth import get_user_model
       python3 = Interpreter(name='Python 3', path='/bin/python3', arguments=['-u'])
       server = Server(title='Remote', hostname='foo.invalid', port=22)
       user = get_user_model()(username='john')

    >>> from django_remote_submission.models import Job
    >>> job = Job(
    ...     title='My Job',
    ...     program='print("hello world")',
    ...     remote_directory='/tmp/',
    ...     remote_filename='foobar.py',
    ...     owner=user,
    ...     server=server,
    ...     interpreter=python3,
    ... )
    >>> job
    <Job: My Job>

    """

    title = models.CharField(
        _('Job Name'),
        help_text=_('The human-readable name of the job'),
        max_length=250,
    )

    uuid = models.UUIDField(
        _('Job UUID'),
        help_text=_('A unique identifier for use in grouping Result files'),
        default=uuid.uuid4,
        editable=False,
    )

    program = models.TextField(
        _('Job Program'),
        help_text=_('The actual program to run (starting with a #!)'),
    )

    STATUS = Choices(
        ('initial', _('initial')),
        ('submitted', _('submitted')),
        ('success', _('success')),
        ('failure', _('failure')),
    )
    status = StatusField(
        _('Job Status'),
        help_text=_('The current status of the program'),
        default=STATUS.initial,
    )

    remote_directory = models.CharField(
        _('Job Remote Directory'),
        help_text=_('The directory on the remote host to store the program'),
        max_length=250,
    )

    remote_filename = models.CharField(
        _('Job Remote Filename'),
        help_text=_('The filename to store the program to (e.g. reduce.py)'),
        max_length=250,
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.PROTECT,
        related_name='jobs',
        verbose_name=_('Job Owner'),
        help_text=_('The user that owns this job'),
    )

    server = models.ForeignKey(
        'Server',
        models.PROTECT,
        related_name='jobs',
        verbose_name=_('Job Server'),
        help_text=_('The server that this job will run on'),
    )

    interpreter = models.ForeignKey(
        Interpreter,
        models.PROTECT,
        related_name='jobs',
        verbose_name=_('Job Interpreter'),
        help_text=_('The interpreter that this job will run on'),
    )

    class Meta:  # noqa: D101
        verbose_name = _('job')
        verbose_name_plural = _('jobs')

    def __str__(self):
        """Convert model to string, e.g. ``"My Job"``."""
        return '{self.title}'.format(self=self)

    def clean(self):
        """Ensure that the selected interpreter exists on the server.

        To use effectively, add this to the
        :func:`django.db.models.signals.pre_save` signal for the :class:`Job`
        model.

        """
        available_interpreters = self.server.interpreters.all()
        if self.interpreter not in available_interpreters:
            raise ValidationError(_('The Interpreter picked is not valid for this server. '))
            #'Please, choose one from: {0!s}.').format(available_interpreters))
        else:
            cleaned_data = super(Job, self).clean()
            return cleaned_data


@python_2_unicode_compatible
class Log(models.Model):
    """Encapsulates a log message printed from a job.

    .. testsetup::

       from django_remote_submission.models import Job, Server, Interpreter
       from django.contrib.auth import get_user_model
       python3 = Interpreter(name='Python 3', path='/bin/python3', arguments=['-u'])
       server = Server(title='Remote', hostname='foo.invalid', port=22)
       user = get_user_model()(username='john')
       job = Job(title='My Job', program='print("hello world")',
           remote_directory='/tmp/', remote_filename='foobar.py',
           owner=user, server=server, interpreter=python3,
       )

    >>> from django_remote_submission.models import Log
    >>> from datetime import datetime
    >>> log = Log(
    ...     time=datetime(year=2017, month=1, day=2, hour=3, minute=4, second=5),
    ...     content='Hello World',
    ...     stream='stdout',
    ...     job=job,
    ... )
    >>> log
    <Log: 2017-01-02 03:04:05 My Job>

    """

    time = AutoCreatedField(
        _('Log Time'),
        help_text=_('The time this log was created'),
    )

    content = models.TextField(
        _('Log Content'),
        help_text=_('The content of this log message'),
    )

    STD_STREAM_CHOICES = (
        ('stdout', _('stdout')),
        ('stderr', _('stderr')),
    )
    stream = models.CharField(
        _('Standard Stream'),
        max_length=6,
        choices=STD_STREAM_CHOICES,
        help_text=_('Output communication channels. Either stdout or stderr.'),
        default='stdout',
    )

    job = models.ForeignKey(
        'Job',
        models.CASCADE,
        related_name='logs',
        verbose_name=_('Log Job'),
        help_text=_('The job this log came from'),
    )

    class Meta:  # noqa: D101
        verbose_name = _('log')
        verbose_name_plural = _('logs')

    def __str__(self):
        """Convert model to string, e.g. ``"2017-01-02 03:04:05 My Job"``."""
        return '{self.time} {self.job}'.format(self=self)


def job_result_path(instance, filename):
    """Produce the path to locally store the job results.

    :param Result instance: the :class:`Result` instance to produce the path
        for
    :param str filename: the original filename

    """
    return 'results/{}/{}'.format(instance.job.uuid, filename)


@python_2_unicode_compatible
class Result(TimeStampedModel):
    """Encapsulates a resulting file produced by a job.

    .. testsetup::

       from django_remote_submission.models import Job, Server, Interpreter
       from django.contrib.auth import get_user_model
       python3 = Interpreter(name='Python 3', path='/bin/python3', arguments=['-u'])
       server = Server(title='Remote', hostname='foo.invalid', port=22)
       user = get_user_model()(username='john')
       job = Job(title='My Job', program='print("hello world")',
           remote_directory='/tmp/', remote_filename='foobar.py',
           owner=user, server=server, interpreter=python3,
       )

    >>> from django_remote_submission.models import Result
    >>> result = Result(
    ...     remote_filename='1.txt',
    ...     job=job,
    ... )
    >>> result
    <Result: 1.txt <My Job>>

    """

    remote_filename = models.TextField(
        _('Remote Filename'),
        help_text=_('The filename on the remote server for this result, '
                    'relative to the remote directory of the job'),
        max_length=250,
    )

    local_file = models.FileField(
        _('Local Filename'),
        help_text=_('The filename on the local server for this result'),
        upload_to=job_result_path,
        max_length=250,
    )

    job = models.ForeignKey(
        'Job',
        models.CASCADE,
        related_name='results',
        verbose_name=_('Result Job'),
        help_text=_('The job this result came from'),
    )

    class Meta:  # noqa: D101
        verbose_name = _('result')
        verbose_name_plural = _('results')

    def __str__(self):
        """Convert model to string, e.g. ``"1.txt <My Job>"``."""
        return '{self.remote_filename} <{self.job}>'.format(self=self)
