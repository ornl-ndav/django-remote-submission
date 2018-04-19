from django.views.generic import TemplateView, DetailView, ListView
from django.conf import settings
from django.http import HttpResponse

from django_remote_submission.models import Interpreter, Server, Job, Log
from django_remote_submission.tasks import submit_job_to_server
from django.contrib.auth.mixins import LoginRequiredMixin

import textwrap
import logging

logger = logging.getLogger(__name__)  # pylint: disable=C0103


class IndexView(LoginRequiredMixin, TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['job_list'] = Job.objects.all()
        context['server_list'] = Server.objects.all()
        context['Log_list'] = Log.objects.all()
        return context


class ServerDetail(LoginRequiredMixin, DetailView):
    model = Server


class ServerList(LoginRequiredMixin, ListView):
    model = Server


class JobDetail(LoginRequiredMixin, DetailView):
    model = Job


class JobList(LoginRequiredMixin, ListView):
    model = Job


class ExampleJobLogView(LoginRequiredMixin, TemplateView):
    template_name = 'example_job_log.html'

    def get_context_data(self, **kwargs):
        context = super(ExampleJobLogView, self).get_context_data(**kwargs)
        context['job_pk'] = kwargs['job_pk']
        return context


class ExampleJobStatusView(LoginRequiredMixin, TemplateView):
    template_name = 'example_job_status.html'

    def post(self, request, *args, **kwargs):
        (interpreter, _) = Interpreter.objects.get_or_create(
            name='Python',
            path=settings.EXAMPLE_PYTHON_PATH,
            arguments=settings.EXAMPLE_PYTHON_ARGUMENTS,
        )

        (server, _) = Server.objects.get_or_create(
            title='Example Server',
            hostname=settings.EXAMPLE_SERVER_HOSTNAME,
            port=settings.EXAMPLE_SERVER_PORT,
        )

        logger.debug("Running job in {} using {}".format(server, interpreter))

        num_jobs = len(Job.objects.all())

        program = textwrap.dedent('''\
        from __future__ import print_function
        import time
        for i in range(10):
            with open('django_remote_submission_example_out_{}.txt'.format(i), 'wt') as f:
                print('Line {}'.format(i), file=f)
                print('Line {}'.format(i))
            time.sleep(1)
        ''')

        (job, _) = Job.objects.get_or_create(
            title='Example Job #{}'.format(num_jobs),
            program=program,
            remote_directory=settings.EXAMPLE_REMOTE_DIRECTORY,
            remote_filename=settings.EXAMPLE_REMOTE_FILENAME,
            owner=request.user,
            server=server,
            interpreter=interpreter,
        )

        submit_job_to_server.delay(
            job_pk=job.pk,
            password=settings.EXAMPLE_REMOTE_PASSWORD,
            username=settings.EXAMPLE_REMOTE_USER,
        )

        return HttpResponse('success')
