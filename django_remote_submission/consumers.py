"""Manage websocket connections."""
# -*- coding: utf-8 -*-
import json

from channels import Group
from channels.auth import channel_session_user_from_http, channel_session_user

from .models import Job

import json


@channel_session_user_from_http
def ws_connect(message):
    last_jobs = message.user.jobs.order_by('-modified')[:10]

    for job in last_jobs:
        message.reply_channel.send({
            'text': json.dumps({
                'job_id': job.id,
                'title': job.title,
                'status': job.status,
                'modified': job.modified.isoformat(),
            }),
        })

    Group('job-user-{}'.format(message.user.username)).add(
        message.reply_channel,
    )


@channel_session_user
def ws_disconnect(message):
    Group('job-user-{}'.format(message.user.username)).discard(
        message.reply_channel,
    )
