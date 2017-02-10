"""Attach signals to this app's models."""
# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels import Group

from .models import Job


@receiver(post_save, sender=Job, dispatch_uid='update_job_status_listeners')
def update_job_status_listeners(sender, instance, **kwargs):
    Group('job-user-{}'.format(instance.owner.username)).send({
        'text': json.dumps({
            'job_id': instance.id,
            'title': instance.title,
            'status': instance.status,
        }),
    })
