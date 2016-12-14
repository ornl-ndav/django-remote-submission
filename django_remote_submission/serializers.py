# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import Server, Job, Log


class ServerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Server
        fields = ('id', 'title', 'hostname')


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'title', 'program', 'status', 'owner', 'server')


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ('id', 'time', 'content', 'stream', 'job')
