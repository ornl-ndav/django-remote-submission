# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ValidationError

from model_utils import Choices
from model_utils.fields import StatusField, AutoCreatedField
from model_utils.models import TimeStampedModel

@python_2_unicode_compatible
class Interpreter(TimeStampedModel):
    name = models.CharField(
        _('Interpreter Name'),
        help_text=_('The human-readable name of the interpreter'),
        max_length=100,
    )

    path = models.CharField(
        _('Command Full Path'),
        help_text=_('The full path of the interpreter path and additional parameters.'),
        max_length=256,
    )

    class Meta:
        verbose_name = _('interpreter')
        verbose_name_plural = _('interpreters')

    def __str__(self):
        return '{self.name} ({self.path})'.format(self=self)

@python_2_unicode_compatible
class Server(TimeStampedModel):
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

    class Meta:
        verbose_name = _('server')
        verbose_name_plural = _('servers')

    def __str__(self):
        return '{self.title} <{self.hostname}:{self.port}>'.format(self=self)


@python_2_unicode_compatible
class Job(TimeStampedModel):
    title = models.CharField(
        _('Job Name'),
        help_text=_('The human-readable name of the job'),
        max_length=250,
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

    class Meta:
        verbose_name = _('job')
        verbose_name_plural = _('jobs')

    def __str__(self):
        return '{self.title}'.format(self=self)

    def clean(self):
        '''
        Makes sure the interpreter exists for this Server
        This only works for the form job creation!
        TODO: Put this in the pre_save signal
        '''
        available_interpreters = self.server.interpreters.all()
        if self.interpreter not in available_interpreters:
            raise ValidationError(_('The Interpreter picked is not valid for this server. '))
            #'Please, choose one from: {0!s}.').format(available_interpreters))
        else:
            cleaned_data = super(Job, self).clean()
            return cleaned_data


@python_2_unicode_compatible
class Log(models.Model):

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

    class Meta:
        verbose_name = _('log')
        verbose_name_plural = _('logs')

    def __str__(self):
        return '{self.time} {self.job}'.format(self=self)


def job_result_path(instance, filename):
    return 'job_{}/{}'.format(instance.job.id, filename)


@python_2_unicode_compatible
class Result(TimeStampedModel):
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

    class Meta:
        verbose_name = _('result')
        verbose_name_plural = _('results')

    def __str__(self):
        return '{self.remote_filename} <{self.job}>'.format(self=self)
