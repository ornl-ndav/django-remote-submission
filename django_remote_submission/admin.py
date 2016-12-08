# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.utils.translation import ungettext_lazy as _
from django.shortcuts import render
from django.http.response import HttpResponseRedirect

from .models import Server, Job, Log, Interpreter
from .tasks import submit_job_to_server

@admin.register(Interpreter)
class InterpreterAdmin(admin.ModelAdmin):
    pass

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    filter_horizontal = ('interpreters',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    actions = ['submit_to_server']

    class RequestPasswordForm(forms.Form):
        _selected_action = forms.CharField(
            widget=forms.MultipleHiddenInput,
            required=False,
        )
        action = forms.CharField(
            widget=forms.HiddenInput,
            required=False,
        )
        select_across = forms.BooleanField(
            widget=forms.HiddenInput,
            required=False,
        )

        username = forms.CharField(required=False)
        password = forms.CharField(widget=forms.PasswordInput)

    def submit_to_server(self, request, queryset):
        form = None

        if 'apply' in request.POST:
            form = JobAdmin.RequestPasswordForm(request.POST)

            if form.is_valid():
                password = form.cleaned_data['password']
                username = form.cleaned_data['username']

                count = 0
                for job in queryset:
                    submit_job_to_server.delay(
                        job_pk=job.pk,
                        password=password,
                        username=username,
                    )
                    count += 1

                message = _(
                    'Successfully submitted %(count)s job',
                    'Successfully submitted %(count)s jobs',
                    count,
                ) % {
                    'count': count,
                }

                self.message_user(request, message)
                return HttpResponseRedirect(request.get_full_path())

        if not form:
            selected_action = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
            index = int(request.POST.get('index', 0))
            form = JobAdmin.RequestPasswordForm(initial={
                admin.ACTION_CHECKBOX_NAME: selected_action,
                'select_across': request.POST['select_across'],
                'action': request.POST['action'],
            })

        return render(
            request,
            'admin/django_remote_submission/submit_to_server.html',
            {
                'jobs': queryset,
                'form': form,
            },
        )


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    pass
