"""Attach signals to this app's models."""
# -*- coding: utf-8 -*-
import json
import logging

import channels.layers
from asgiref.sync import async_to_sync

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Job, Log


logger = logging.getLogger(__name__)  # pylint: disable=C0103


def send_message(event):
    '''
    Call back function to send message to the browser
    '''
    message = event['text']
    channel_layer = channels.layers.get_channel_layer()
    # Send message to WebSocket
    async_to_sync(channel_layer.send)(text_data=json.dumps(
        message
    ))


@receiver(post_save, sender=Job, dispatch_uid='update_job_status_listeners')
def update_job_status_listeners(sender, instance, **kwargs):
    '''
    Sends job status to the browser when a Job is modified
    '''

    logger.debug("Job modified: {} :: status = {}.".format(
        instance, instance.status))

    user = instance.owner
    group_name = 'job-user-{}'.format(user.username)

    message = {
        'job_id': instance.id,
        'title': instance.title,
        'status': instance.status,
        'modified': instance.modified.isoformat(),
    }

    channel_layer = channels.layers.get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_message',
            'text': message
        }
    )


@receiver(post_save, sender=Log, dispatch_uid='update_job_log_listeners')
def update_job_log_listeners(sender, instance, **kwargs):
    '''
    Sends job status to the browser when a Log is modified
    '''

    logger.debug("Log modified: {} :: content = {}.".format(
        instance, instance.content))

    job_pk = instance.job.id
    group_name = 'job-log-{}'.format(job_pk)

    message = {
        'log_id': instance.id,
        'time': instance.time.isoformat(),
        'content': instance.content,
        'stream': instance.stream,
    }

    channel_layer = channels.layers.get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'send_message',
            'text': message
        }
    )
