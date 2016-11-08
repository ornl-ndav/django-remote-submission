# -*- coding: utf-8 -*-
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    UpdateView,
    ListView
)

from .models import (
	Server,
	Job,
	JobState,
)


class ServerCreateView(CreateView):

    model = Server


class ServerDeleteView(DeleteView):

    model = Server


class ServerDetailView(DetailView):

    model = Server


class ServerUpdateView(UpdateView):

    model = Server


class ServerListView(ListView):

    model = Server


class JobCreateView(CreateView):

    model = Job


class JobDeleteView(DeleteView):

    model = Job


class JobDetailView(DetailView):

    model = Job


class JobUpdateView(UpdateView):

    model = Job


class JobListView(ListView):

    model = Job


class JobStateCreateView(CreateView):

    model = JobState


class JobStateDeleteView(DeleteView):

    model = JobState


class JobStateDetailView(DetailView):

    model = JobState


class JobStateUpdateView(UpdateView):

    model = JobState


class JobStateListView(ListView):

    model = JobState

