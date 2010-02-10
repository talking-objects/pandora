# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
# Django settings for oxdb project.
import os
from os.path import join

SITENAME = 'Oxdb'
URL = 'Oxdb.org'

PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
JSON_DEBUG = False

ADMINS = (
     ('j', 'j@mailb.org'),
)

DEFAULT_FROM_EMAIL='bot@0xdb.org'

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'dev.sqlite'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

#CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

#rabbitmq connection settings
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 5672
BROKER_USER = "oxdb"
BROKER_PASSWORD = "0xdb"
BROKER_VHOST = "/oxdb"

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'
TIME_ZONE = 'Asia/Kolkata'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
APPEND_SLASH = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = join(PROJECT_ROOT, 'media')
STATIC_ROOT = join(PROJECT_ROOT, 'static')
TESTS_ROOT = join(PROJECT_ROOT, 'tests')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

STATIC_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'oxdjango.middleware.ExceptionMiddleware',
)

ROOT_URLCONF = 'oxdb.urls'

TEMPLATE_DIRS = (
    join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.humanize',
    'django_extensions',
    'devserver',
#    'south',

    'app',
    'backend',
    'oxuser',
)

AUTH_PROFILE_MODULE = 'oxuser.UserProfile'

#Video encoding settings
VIDEO_PROFILE = 'low' # possible values low, mid or high
VIDEO_ENCODING = {
    'low': {'height': 96, 'videoBitrate': 180, 'softTarget': True,
            'samplerate': 44100, 'audioQuality': -1, 'channels': 1, 'noUpscaling': True},
    'mid': {'maxSize': 320, 'videoBitrate': 500,
            'samplerate': 44100, 'audioQuality': 0, 'channels': 1, 'noUpscaling': True},
    'high': {'profile': 'padma'}
}

#overwrite default settings with local settings
try:
    from local_settings import *
except ImportError:
    pass

# Make this unique, creates random key first at first time.
try:
    SECRET_KEY
except NameError:
    SECRET_FILE = os.path.join(PROJECT_ROOT, 'secret.txt')
    try:
        SECRET_KEY = open(SECRET_FILE).read().strip()
    except IOError:
        try:
            from random import choice
            SECRET_KEY = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
            secret = file(SECRET_FILE, 'w')
            secret.write(SECRET_KEY)
            secret.close()
        except IOError:
            Exception('Please create a %s file with random characters to generate your secret key!' % SECRET_FILE)

