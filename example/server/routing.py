from channels.routing import include


channel_routing = [
    include('django_remote_submission.routing.application', path=r'^'),
]
