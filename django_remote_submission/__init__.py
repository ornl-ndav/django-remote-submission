from django.db.backends.signals import connection_created
from django.db import connections

__version__ = '0.2.0'

default_app_config = 'django_remote_submission.apps.DjangoRemoteSubmissionConfig'

def activate_pragmas(sender, connection, **kwargs):
    """
    Runs PRAGMA commands in SQLite
    """
    if connection.vendor == 'sqlite':
        connections['default'].allow_thread_sharing = True
        cursor = connection.cursor()
        cursor.execute('PRAGMA busy_timeout = 30000;')
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute("PRAGMA main.wal_checkpoint(PASSIVE);")

connection_created.connect(activate_pragmas)

