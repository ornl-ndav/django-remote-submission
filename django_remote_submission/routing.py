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


from django.urls import re_path

from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

from .consumers import JobUserConsumer, JobLogConsumer


# The channel routing defines what connections get handled by what consumers,
# selecting on either the connection type (ProtocolTypeRouter) or properties
# of the connection's scope (like URLRouter, which looks at scope["path"])
# For more, see http://channels.readthedocs.io/en/latest/topics/routing.html
application = ProtocolTypeRouter({

    # Channels will do this for you automatically. It's included here as an example.
    # "http": AsgiHandler,

    # Route all WebSocket requests to our custom chat handler.
    # We actually don't need the URLRouter here, but we've put it in for
    # illustration. Also note the inclusion of the AuthMiddlewareStack to
    # add users and sessions - see http://channels.readthedocs.io/en/latest/topics/authentication.html
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            re_path(r'^/job-user/$', JobUserConsumer),
            re_path(r'^/job-log/(?P<job_pk>[0-9]+)/$', JobLogConsumer),
        ]),
    ),

})