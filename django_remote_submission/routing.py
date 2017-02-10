from channels.routing import route
from .consumers import ws_connect, ws_disconnect


channel_routing = [
    route('websocket.connect', ws_connect, path=r'^/job-user/$'),
    route('websocket.disconnect', ws_disconnect, path=r'^/job-user/$'),
]
