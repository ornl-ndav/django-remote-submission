# """Manage websocket connections."""
# # -*- coding: utf-8 -*-
# import json

# from channels import Group
# from channels.auth import channel_session_user_from_http, channel_session_user

# from .models import Job

# @channel_session_user_from_http
# def ws_job_status_connect(message):
#     last_jobs = message.user.jobs.order_by('-modified')[:10]

#     for job in last_jobs:
#         message.reply_channel.send({
#             'text': json.dumps({
#                 'job_id': job.id,
#                 'title': job.title,
#                 'status': job.status,
#                 'modified': job.modified.isoformat(),
#             }),
#         })

#     Group('job-user-{}'.format(message.user.username)).add(
#         message.reply_channel,
#     )


# @channel_session_user
# def ws_job_status_disconnect(message):
#     Group('job-user-{}'.format(message.user.username)).discard(
#         message.reply_channel,
#     )


# @channel_session_user_from_http
# def ws_job_log_connect(message, job_pk):
#     job = Job.objects.get(pk=job_pk)

#     logs = job.logs.order_by('time')

#     for log in logs:
#         message.reply_channel.send({
#             'text': json.dumps({
#                 'log_id': log.id,
#                 'time': log.time.isoformat(),
#                 'content': log.content,
#                 'stream': log.stream,
#             }),
#         })

#     Group('job-log-{}'.format(job.id)).add(
#         message.reply_channel,
#     )


# @channel_session_user
# def ws_job_log_disconnect(message, job_pk):
#     job = Job.objects.get(pk=job_pk)

#     Group('job-log-{}'.format(job.id)).discard(
#         message.reply_channel,
#     )

from pprint import pprint

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class JobUserConsumer(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        print("connect")

        # Are they logged in?
        if self.scope["user"].is_anonymous:
            # Reject the connection
            await self.close()
        else:
            # Accept the connection
            await self.accept()


    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        print("disconnect")
        pprint(code)


    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        print("receive_json")
        pprint(content)
        pprint(kwargs)


class JobLogConsumer(AsyncJsonWebsocketConsumer):
    """
    This chat consumer handles websocket connections for chat clients.
    It uses AsyncJsonWebsocketConsumer, which means all the handling functions
    must be async functions, and any sync work (like ORM access) has to be
    behind database_sync_to_async or sync_to_async. For more, read
    http://channels.readthedocs.io/en/latest/topics/consumers.html
    """

    ##### WebSocket event handlers

    async def connect(self):
        """
        Called when the websocket is handshaking as part of initial connection.
        """
        print("connect")

        # Are they logged in?
        if self.scope["user"].is_anonymous:
            # Reject the connection
            await self.close()
        else:
            # Accept the connection
            await self.accept()


    async def disconnect(self, code):
        """
        Called when the WebSocket closes for any reason.
        """
        print("disconnect")
        pprint(code)


    async def receive_json(self, content, **kwargs):
        """
        Called when we get a text frame. Channels will JSON-decode the payload
        for us and pass it as the first argument.
        """
        # Messages will have a "command" key we can switch on
        print("receive_json")
        pprint(content)
        pprint(kwargs)