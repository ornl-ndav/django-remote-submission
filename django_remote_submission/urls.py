"""Provide default route mappings for serializers."""
# -*- coding: utf-8 -*-
from rest_framework.routers import DefaultRouter
from django.conf.urls import url

from .views import (
    ServerViewSet, JobViewSet, LogViewSet, JobUserStatus, ResultViewSet
)


router = DefaultRouter()
router.register(r'servers', ServerViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'logs', LogViewSet)
router.register(r'results', ResultViewSet)

urlpatterns = router.urls + [
    url(r'^job-user-status/$', JobUserStatus.as_view()),
]
"""The URL patterns for the defined serializers."""
