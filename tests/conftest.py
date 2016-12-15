from django.conf import settings

def pytest_configure():
    settings.configure(
        DEBUG=True,
        USE_TZ=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "OPTIONS": { # for concurrent writes
                    "timeout": 30000, # ms
                }
            }
        },
        ROOT_URLCONF="django_remote_submission.urls",
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sites",
            "django_remote_submission",
        ],
        SITE_ID=1,
        MIDDLEWARE_CLASSES=(),
        LOGGING = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'verbose': {
                    'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
                },
                'simple': {
                    'format': '%(levelname)s :: %(message)s'
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'formatter': 'simple',
                },
            },
            'loggers': {
                'django': {
                    'handlers': ['console'],
                    'level': 'CRITICAL',
                    'propagate': True,
                },
                'django_remote_submission': {
                    'handlers': ['console'],
                    'level': 'CRITICAL',
                    'propagate': True,
                },
            },
        },
    )
