"""Provide default views for REST API."""
# -*- coding: utf-8 -*-
import django_filters

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django.views.generic import TemplateView

from .models import Server, Job, Log, Result
from .serializers import (
    ServerSerializer, JobSerializer, LogSerializer, ResultSerializer
)

from django_filters.rest_framework import DjangoFilterBackend
from django.db import models

class StandardPagination(PageNumberPagination):
    """Change the default page size."""

    page_size = 10

#
# View Sets
#


class ServerViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Server` instances."""

    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('title', 'hostname', 'port')
    pagination_class = StandardPagination


class JobViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Job` instances."""

    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('title', 'program', 'status', 'owner', 'server')
    pagination_class = StandardPagination


class LogViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Log` instances."""

    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('time', 'content', 'stream', 'job')
    pagination_class = StandardPagination


class ResultViewSet(viewsets.ModelViewSet):
    """Allow users to create, read, and update :class:`Result` instances."""

    queryset = Result.objects.all()
    serializer_class = ResultSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('remote_filename', 'job')  # 'local_file',
    pagination_class = StandardPagination

    class Meta:
        filter_overrides = {
            models.FileField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }

#
# Templates
#


class JobUserStatus(TemplateView):
    """Show status of all of user's jobs with live updates."""

    template_name = "django_remote_submission/job-user-status.html"
