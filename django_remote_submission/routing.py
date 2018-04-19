# from channels.routing import route
# from .consumers import (
#     ws_job_status_connect, ws_job_status_disconnect,
#     ws_job_log_connect, ws_job_log_disconnect,
# )


# channel_routing = [
#     route('websocket.connect', ws_job_status_connect,       path=r'^/job-user/$'),
#     route('websocket.disconnect', ws_job_status_disconnect, path=r'^/job-user/$'),
#     route('websocket.connect', ws_job_log_connect,       path=r'^/job-log/(?P<job_pk>[0-9]+)/$'),
#     route('websocket.disconnect', ws_job_log_disconnect, path=r'^/job-log/(?P<job_pk>[0-9]+)/$'),
# ]


from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from .consumers import JobUserConsumer, JobLogConsumer


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        URLRouter([
            path('ws/job-user/', JobUserConsumer),
            path('ws/job-log/<int:job_pk>/', JobLogConsumer),
        ]),
    ),

})