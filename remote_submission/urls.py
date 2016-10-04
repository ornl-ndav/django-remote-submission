from django.conf.urls import url
from .views import ServerView, IndexView, JobView, JobCreateView

app_name = 'remote_submission'
urlpatterns = [
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^server/$', ServerView.as_view(), name='server'),
    url(r'^job/$', JobView.as_view(), name='job-list'),
    url(r'^job/create/$', JobCreateView.as_view(), name='job-create'),
]
