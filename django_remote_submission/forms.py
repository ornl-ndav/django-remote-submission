# -*- coding: utf-8 -*-
from django import forms

from .models import Server, Job


class ServerForm(forms.ModelForm):
    class Meta:
        model = Server
        fields = ('title', 'hostname')


class JobForm(form.ModelForm):
    class Meta:
        model = Job
        fields = ('title', 'program', 'status', 'server')
