"""Manage websocket connections."""
# -*- coding: utf-8 -*-
import json

from channels import Group
from channels.auth import channel_session_user_from_http, channel_session_user

from .models import Job


@channel_session_user_from_http
def ws_connect(message):
    message.reply_channel.send({
        'accept': True,
    })

    Group('job-user-{}'.format(message.user.username)).add(
        message.reply_channel,
    )


@channel_session_user
def ws_disconnect(message):
    Group('job-user-{}'.format(message.user.username)).discard(
        message.reply_channel,
    )
