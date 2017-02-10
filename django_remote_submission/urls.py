"""Provide default route mappings for serializers."""
# -*- coding: utf-8 -*-
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from .views import ServerViewSet, JobViewSet, LogViewSet, JobUserStatus


router = DefaultRouter()
router.register(r'servers', ServerViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'logs', LogViewSet)

urlpatterns = router.urls + [
    url(r'^job-user-status/$', JobUserStatus.as_view()),
]
"""The URL patterns for the defined serializers."""
