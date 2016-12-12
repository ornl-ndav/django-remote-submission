import sys

try:
    from django.conf import settings
    from django.test.utils import get_runner

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
                    'level': 'INFO',
                    'propagate': True,
                },
                'django_remote_submission': {
                    'handlers': ['console'],
                    'level': 'DEBUG',
                    'propagate': True,
                },
            },
        }
    )

    try:
        import django
        setup = django.setup
    except AttributeError:
        pass
    else:
        setup()

except ImportError:
    import traceback
    traceback.print_exc()
    msg = "To fix this error, run: pip install -r requirements_test.txt"
    raise ImportError(msg)


def run_tests(*test_args):
    if not test_args:
        test_args = ['tests']

    # Run tests
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(test_args)

    if failures:
        sys.exit(bool(failures))


if __name__ == '__main__':
    run_tests(*sys.argv[1:])
