# -*- coding: utf-8 -*-

import time

from django.core.management.base import BaseCommand

import app.monkey_patch
from ... import models


class Command(BaseCommand):
    """
    rebuild sort/search cache for all items.
    """
    help = 'rebuild sort/search cache for all items.'
    args = ''

    def handle(self, **options):
        offset = 0
        chunk = 50
        count = pos = models.Item.objects.count()
        while offset <= count:
            for i in models.Item.objects.all().order_by('id')[offset:offset+chunk]:
                print(pos, i.public_id)
                i.save()
                time.sleep(1) #dont overload db
                pos -= 1
            offset += chunk
            time.sleep(30) #dont overload db
