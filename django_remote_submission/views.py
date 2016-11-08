# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination

from .models import Server, Job, Log
from .serializers import ServerSerializer, JobSerializer, LogSerializer


class StandardPagination(PageNumberPagination):
    page_size = 5


class ServerViewSet(viewsets.ModelViewSet):
    queryset = Server.objects.all()
    serializer_class = ServerSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination


class JobViewSet(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination


class LogViewSet(viewsets.ModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = StandardPagination
