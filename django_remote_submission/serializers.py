"""Provide default serializers for managing this package's models."""
# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import Server, Job, Log, Result


class ServerSerializer(serializers.ModelSerializer):
    """Serialize :class:`django_remote_submission.models.Server` instances.

    >>> from django_remote_submission.serializers import ServerSerializer
    >>> serializer = ServerSerializer(data={
    ...     'id': 1,
    ...     'title': 'My Server',
    ...     'hostname': 'foo.invalid',
    ...     'port': 22,
    ... })
    >>> serializer.is_valid()
    True

    """

    class Meta:  # noqa: D101
        model = Server
        fields = ('id', 'title', 'hostname', 'port')


class JobSerializer(serializers.ModelSerializer):
    """Serialize :class:`django_remote_submission.models.Job` instances.

    >>> from django_remote_submission.serializers import JobSerializer
    >>> serializer = JobSerializer(data={
    ...     'id': 1,
    ...     'title': 'My Job',
    ...     'program': 'print("Hello world")',
    ...     'status': 'INITIAL',
    ...     'owner': 1,
    ...     'server': 1,
    ... })
    >>> serializer.is_valid()  # doctest: +SKIP
    True

    """

    class Meta:  # noqa: D101
        model = Job
        fields = ('id', 'title', 'program', 'status', 'owner', 'server')


class LogSerializer(serializers.ModelSerializer):
    """Serialize :class:`django_remote_submission.models.Log` instances.

    >>> from django_remote_submission.serializers import LogSerializer
    >>> serializer = LogSerializer(data={
    ...     'id': 1,
    ...     'time': '2012-04-23T18:25:43.511Z',
    ...     'content': 'Hello world',
    ...     'stream': 'stdout',
    ...     'job': 1,
    ... })
    >>> serializer.is_valid()  # doctest: +SKIP
    True

    """

    class Meta:  # noqa: D101
        model = Log
        fields = ('id', 'time', 'content', 'stream', 'job')


class ResultSerializer(serializers.ModelSerializer):

    class Meta:  # noqa: D101
        model = Result
        fields = ('id', 'remote_filename', 'local_file', 'job')
