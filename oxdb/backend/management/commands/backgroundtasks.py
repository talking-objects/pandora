# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

import os
from os.path import join, dirname, basename, splitext, exists

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from ... import daemon


class Command(BaseCommand):
    """
    listen to rabbitmq and execute background task.
    """
    help = 'listen to rabbitmq and execute background task.'
    args = ''

    def handle(self, **options):
        daemon.run()

