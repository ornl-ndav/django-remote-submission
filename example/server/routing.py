from channels.routing import include


channel_routing = [
    include('django_remote_submission.routing.channel_routing', path=r'^'),
]
