from django.shortcuts import render
from django.views.generic import TemplateView, FormView
from .models import Server, Job
from .forms import JobForm

class ServerView(TemplateView):
    template_name = 'remote_submission/server.html'

class JobView(TemplateView):
    template_name = 'remote_submission/job.html'

class JobCreateView(FormView):
    template_name = 'remote_submission/job_create.html'
    form_class = JobForm

class IndexView(TemplateView):
    template_name = 'remote_submission/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_jobs'] = Job.objects.order_by('-modified_date')[:5]
        return context
