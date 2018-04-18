# from channels.routing import include


# channel_routing = [
#     include('django_remote_submission.routing.application', path=r'^'),
# ]

from django.conf.urls import url

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

import django_remote_submission.routing


application = ProtocolTypeRouter({

    # WebSocket handler
    "websocket": AuthMiddlewareStack(
        URLRouter([
            url("", django_remote_submission.routing.application),
        ])
    ),
})