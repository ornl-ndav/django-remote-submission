"""Provide default config when installing the application."""

# -*- coding: utf-8 -*-
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class DjangoRemoteSubmissionConfig(AppConfig):
    """Provide basic configuration of this app."""

    name = 'django_remote_submission'
    verbose_name = 'Django Remote Submission'

    def ready(self):
        logger.debug("DjangoRemoteSubmissionConfig Ready!")
        import django_remote_submission.signals
