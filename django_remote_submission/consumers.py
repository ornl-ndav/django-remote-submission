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

import json
from pprint import pprint
from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer, AsyncWebsocketConsumer

from .models import Job
from asgiref.sync import async_to_sync


class JobUserConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        '''
        Creates group, add to the valid channels
        Connects and sends to the browser the last jobs
        '''
        user = self.scope["user"]
        self.group_name = 'job-user-{}'.format(user.username)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_last_jobs(user)

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )


    async def send_last_jobs(self, user):

        last_jobs = user.jobs.order_by('-modified')[:10]

        for job in last_jobs:

            message = {
                'job_id': job.id,
                'title': job.title,
                'status': job.status,
                'modified': job.modified.isoformat(),
            }

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_message',
                    'text': message
                }
            )

    async def send_message(self, event):
        message = event['text']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            message
        ))


class JobLogConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        '''
        Creates group, add to the valid channels
        Connects and sends to the browser the log
        '''
        job_pk = self.scope['url_route']['kwargs']['job_pk']
        self.group_name = 'job-log-{}'.format(job_pk)

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_log(job_pk)

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_log(self, job_pk):

        job = Job.objects.get(pk=job_pk)
        logs = job.logs.order_by('time')

        for log in logs:
            message = {
                    'log_id': log.id,
                    'time': log.time.isoformat(),
                    'content': log.content,
                    'stream': log.stream,
                }

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_message',
                    'text': message
                }
            )

    async def send_message(self, event):
        message = event['text']

        # Send message to WebSocket
        await self.send(text_data=json.dumps(
            message
        ))