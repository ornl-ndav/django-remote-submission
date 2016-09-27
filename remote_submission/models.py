from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
import threading
import paramiko
import io

# Create your models here.

def get_sentinel_user():
    return get_user_model().objects.get_or_create(username='deleted')[0]

def get_sentinel_server():
    return Server.objects.get_or_create(
        name='deleted',
        host='invalid.invalid',
        port='-1',
    )[0]

class Server(models.Model):
    name = models.CharField(
        max_length=128,
    )

    hostname = models.CharField(
        max_length=128,
    )

    port = models.SmallIntegerField(
        default=22,
    )

    class Meta:
        pass

    def __repr__(self):
        return 'Server(name={self.name}, hostname={self.hostname}, port={self.port}'.format(
            self=self,
        )

    def __str__(self):
        return '{self.name}'.format(self=self)

    def get_absolute_url(self):
        return reverse('server-detail', kwargs={'pk': self.pk})

class Job(models.Model):
    name = models.CharField(
        max_length=128,
    )

    server = models.ForeignKey(
        'Server',
        on_delete=models.SET(get_sentinel_server),
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET(get_sentinel_user),
    )

    script = models.TextField(
        max_length=10240,
    )

    remote_user = models.CharField(
        max_length=128,
    )

    is_submitted = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __repr__(self):
        return 'Job(name={self.name}, server={self.server}, owner={self.owner}, is_submitted={self.is_submitted}, is_completed={self.is_completed})'.format(
            self=self,
        )

    def __str__(self):
        return '{self.name}'.format(self=self)

    def get_absolute_url(self):
        return reverse('job-detail', kwargs={'pk': self.pk})

    def run(self, password='failsafe', callback=None):
        def thread():
            client = paramiko.client.SSHClient()
            client.load_system_host_keys()
            client.connect(
                hostname=self.server.hostname,
                port=self.server.port,
                username=self.remote_user,
                password=password,
            )

            sftp = client.open_sftp()
            sftp.putfo(io.StringIO(self.script), '/tmp/foobar.py')

            stdin, stdout, stderr = client.exec_command(
                command='python /tmp/foobar.py',
            )

            out = stdout.read()

            print(out)

            self.is_completed = True

            if callback:
                callback(self)

        if self.is_submitted:
            raise Exception("foobar")

        t = threading.Thread(
            target=thread,
        )
        t.daemon = True
        t.start()

        self.is_submitted = True
