from django.views.generic import TemplateView, DetailView, ListView
from django_remote_submission.models import Server, Job, Log


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
