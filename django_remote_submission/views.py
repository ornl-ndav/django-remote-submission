"""Provide default views for REST API."""
# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.views.generic import TemplateView

from .models import Server, Job, Log
from .serializers import ServerSerializer, JobSerializer, LogSerializer


class StandardPagination(PageNumberPagination):
    """Change the default page size."""

    page_size = 5


class ServerViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Server` instances."""

    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination


class JobViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Job` instances."""

    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination


class LogViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Log` instances."""

    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination


class JobUserStatus(TemplateView):
    """Show status of all of user's jobs with live updates."""

    template_name = "django_remote_submission/job-user-status.html"
