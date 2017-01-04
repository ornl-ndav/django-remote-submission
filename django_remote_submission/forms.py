"""Provide the forms for working with this app's models."""

# -*- coding: utf-8 -*-
from django import forms

from .models import Server, Job


class ServerForm(forms.ModelForm):
    """Provide a form for inputting information about a remote server."""

    class Meta:  # noqa: D101
        model = Server
        fields = ('title', 'hostname')


class JobForm(forms.ModelForm):
    """Provide a form for inputting information about a job."""

    class Meta:  # noqa: D101
        model = Job
        fields = ('title', 'program', 'status', 'server')
