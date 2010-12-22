# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
# Django settings for pan.do/ra project defaults,
# create local_settings.py to overwrite
import os
from os.path import join, normpath

SITENAME = 'Pan.do/ra'
SITEID =   'pandora'
URL =      'pan.do/ra'

PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
JSON_DEBUG = True

#with apache x-sendfile or lighttpd set this to True
XSENDFILE = False

#with nginx X-Accel-Redirect set this to True
XACCELREDIRECT = False

ADMINS = (
     #('admin', 'admin@example.com'),
)

DEFAULT_FROM_EMAIL='admin@' + URL.split('/')[0]
#DEFAULT_FROM_EMAIL='admin@example.com'

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'dev.sqlite'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.


#rabbitmq connection settings
CELERY_RESULT_BACKEND = "database"
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 5672
BROKER_USER = "pandora"
BROKER_PASSWORD = "box"
BROKER_VHOST = "/pandora"
SEND_CELERY_ERROR_EMAILS=False


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Berlin'
#TIME_ZONE = 'Asia/Kolkata'

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
MEDIA_ROOT = normpath(join(PROJECT_ROOT, '..', 'data'))
STATIC_ROOT = normpath(join(PROJECT_ROOT, '..', 'static'))
TESTS_ROOT = join(PROJECT_ROOT, 'tests')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/data/'

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
    'ox.django.middleware.ExceptionMiddleware',
    'ox.django.middleware.ChromeFrameMiddleware',
)

ROOT_URLCONF = 'pandora.urls'

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
    'djcelery',

    'annotaion',
    'app',
    'archive',
    'date',
    'item',
    'itemlist',
    'person',
    'place',
    'text',
    'torrent',
    'user',
    'api',
)

AUTH_PROFILE_MODULE = 'user.UserProfile'

#Video encoding settings
#available profiles: 96p, 270p, 360p, 480p, 720p, 1080p

DEFAULT_SORT = [{"key": "director", "operator": ""}]
DEFAULT_THEME = "classic"

VIDEO_PROFILE = '96p'
VIDEO_DERIVATIVES = []
VIDEO_H264 = False

#Pad.ma
#VIDEO_PROFILE = '480p'
#VIDEO_DERIVATIVES = ['96p', '270p', '360p']
#VIDEO_H264 = False


TRANSMISSON_HOST = 'localhost'
TRANSMISSON_PORT = 9091
TRANSMISSON_USER = 'transmission'
TRANSMISSON_PASSWORD = 'transmission'


#Movie related settings
REVIEW_WHITELIST = {
    u'filmcritic.com': u'Filmcritic',
    u'metacritic.com': u'Metacritic',
    u'nytimes.com': u'New York Times',
    u'rottentomatoes.com': u'Rotten Tomatoes',
    u'salon.com': u'Salon.com',
    u'sensesofcinema.com': u'Senses of Cinema',
    u'villagevoice.com': u'Village Voice'
}

#list of poster services, https://wiki.0x2620.org/wiki/pandora/posterservice
POSTER_SERVICES = []
POSTER_PRECEDENCE = (
    'local',
    'criterion.com',
    'wikipedia.org',
    'impawards.com',
    'movieposterdb.com',
    'imdb.com',
    'allmovie.com',
    'other'
)

#0xdb.org
#POSTER_SERVICES=['http://data.0xdb.org/poster/']

#copy scripts and adjust to customize
ITEM_POSTER = join('scripts', 'oxdb_poster')
#ITEM_POSTER = join('scripts', 'padma_poster')
ITEM_ICON   = join('scripts', 'item_icon')
LIST_ICON   = join('scripts', 'list_icon')

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

