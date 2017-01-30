"""Attach signals to this app's models."""
# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from channels import Group

from .models import Job


@receiver(post_save, sender=Job)
def update_job_status_listeners(sender, **kwargs):
    Group('job-user-{}'.format(sender.owner.username)).send({
        'text': json.dumps({
            'job_id': sender.id,
            'status': sender.status,
        }),
    })
