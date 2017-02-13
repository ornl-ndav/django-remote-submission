"""example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from .views import (
    IndexView, ServerDetail, ServerList, JobDetail, JobList,
    ExampleJobStatusView, ExampleJobLogView,
)


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^example/$', ExampleJobStatusView.as_view(), name='example'),
    url(r'^logs/(?P<job_pk>[0-9]+)/$', ExampleJobLogView.as_view(), name='logs'),
    url(r'^servers/$', ServerList.as_view(), name='server-list'),
    url(r'^servers/(?P<pk>[0-9]+)/$', ServerDetail.as_view(), name='server-detail'),
    url(r'^jobs/$', JobList.as_view(), name='job-list'),
    url(r'^api/', include('django_remote_submission.urls')),
]
