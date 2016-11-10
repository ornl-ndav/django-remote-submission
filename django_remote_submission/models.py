# -*- coding: utf-8 -*-

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible

from model_utils import Choices
from model_utils.fields import StatusField, AutoCreatedField
from model_utils.models import TimeStampedModel


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
        ('edited', _('edited')),
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
        _('Job Owner'),
        help_text=_('The user that owns this job'),
    )

    server = models.ForeignKey(
        'Server',
        models.PROTECT,
        _('Job Server'),
        help_text=_('The server that this job will run on'),
    )

    class Meta:
        verbose_name = _('job')
        verbose_name_plural = _('jobs')

    def __str__(self):
        return '{self.title}'.format(self=self)


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

    job = models.ForeignKey(
        'Job',
        models.CASCADE,
        _('Log Job'),
        help_text=_('The job this log came from'),
    )

    class Meta:
        verbose_name = _('log')
        verbose_name_plural = _('logs')

    def __str__(self):
        return '{self.time} {self.job}'.format(self=self)
