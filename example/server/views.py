from django.views.generic import TemplateView, DetailView, ListView
from django.conf import settings
from django.http import HttpResponse

from django_remote_submission.models import Interpreter, Server, Job, Log
from django_remote_submission.tasks import submit_job_to_server

import textwrap


class IndexView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['job_list'] = Job.objects.all()
        context['server_list'] = Server.objects.all()
        context['Log_list'] = Log.objects.all()
        return context


class ServerDetail(DetailView):
    model = Server


class ServerList(ListView):
    model = Server


class JobDetail(DetailView):
    model = Job


class JobList(ListView):
    model = Job


class ExampleJobLogView(TemplateView):
    template_name = 'example_job_log.html'

    def get_context_data(self, **kwargs):
        context = super(ExampleJobLogView, self).get_context_data(**kwargs)
        context['job_pk'] = kwargs['job_pk']
        return context


class ExampleJobStatusView(TemplateView):
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

        num_jobs = len(Job.objects.all())

        program = textwrap.dedent('''\
        import time
        for i in range(5):
            with open('{}.txt'.format(i), 'wt') as f:
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

        _ = submit_job_to_server.delay(
            job.pk,
            settings.EXAMPLE_REMOTE_USER,
            settings.EXAMPLE_REMOTE_PASSWORD,
        )

        return HttpResponse('success')
