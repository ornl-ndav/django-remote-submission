from channels.routing import route
from .consumers import (
    ws_job_status_connect, ws_job_status_disconnect,
    ws_job_log_connect, ws_job_log_disconnect,
)


channel_routing = [
    route('websocket.connect', ws_job_status_connect, path=r'^/job-user/$'),
    route('websocket.disconnect', ws_job_status_disconnect, path=r'^/job-user/$'),
    route('websocket.connect', ws_job_log_connect,
          path=r'^/job-log/(?P<job_pk>[0-9]+)/$'),
    route('websocket.disconnect', ws_job_log_disconnect,
          path=r'^/job-log/(?P<job_pk>[0-9]+)/$'),
]
