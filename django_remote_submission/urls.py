# -*- coding: utf-8 -*-
from rest_framework.routers import DefaultRouter

from .views import ServerViewSet, JobViewSet, LogViewSet


router = DefaultRouter()
router.register(r'servers', ServerViewSet)
router.register(r'jobs', JobViewSet)
router.register(r'logs', LogViewSet)

urlpatterns = router.urls
