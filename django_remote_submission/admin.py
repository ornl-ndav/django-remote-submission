"""Provide an admin interface for managing jobs."""

# -*- coding: utf-8 -*-
from django.contrib import admin
from django import forms
from django.utils.translation import ungettext_lazy as _
from django.shortcuts import render
from django.http.response import HttpResponseRedirect

from .models import Server, Job, Log, Interpreter, Result
from .tasks import submit_job_to_server

@admin.register(Interpreter)
class InterpreterAdmin(admin.ModelAdmin):
    """Manage interpreters with default admin interface."""
    pass


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    """Manage Results with default admin interface."""
    pass


@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    """Manage servers and allow selecting interpreters from available ones."""

    filter_horizontal = ('interpreters',)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Manage jobs with ability to submit the job from the interface.

    To submit a job:

    1. Make sure it is created and has all the correct fields, including the
    program, server, and interpreter.

    2. Go back to the main job index.

    3. Select the job.

    4. Select "Submit to server" from the actions list.

    5. Put in the username of the person to execute the job (or blank if it's
    the same as the owner's Django username).

    6. Put in the password of the user to execute the job.

    7. Click "Submit to Server".

    """

    actions = ['submit_to_server']

    class RequestPasswordForm(forms.Form):
        """Provide a form to put in the username and password of job's owner.

        The hidden inputs are requried to work with the action list in the
        admin interface. These were hard to find because having a second page
        for actions in Django isn't very well documented, and information is
        spread through a handful of blog posts.

        """

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
        """Submit job to server via an admin interface action."""
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
            # This part is required to make the intermediate page work with the
            # Django actions.
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
    """Manage logs with the default admin interface."""

    pass
