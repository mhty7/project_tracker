from .settings import *

DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'ngo-django',
        'USER': 'ngo',
        'PASSWORD': 'ngo',
        'HOST': 'localhost',
        'PORT':'5432',
        'ATOMIC_REQUESTS':True,
    }
}