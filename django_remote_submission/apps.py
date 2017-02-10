"""Provide default config when installing the application."""

# -*- coding: utf-8 -*-
from django.apps import AppConfig


class DjangoRemoteSubmissionConfig(AppConfig):
    """Provide basic configuration of this app."""

    name = 'django_remote_submission'
    verbose_name = 'Django Remote Submission'

    def ready(self):
        import django_remote_submission.signals
