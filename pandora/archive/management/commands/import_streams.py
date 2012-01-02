# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from django.core.management.base import BaseCommand
from django.conf import settings
import os
from glob import glob

from celery.task import task

from ... import models, extract


@task(queue="encoding")
def update_stream(id):
    s = models.Stream.objects.get(pk=id)
    if not glob("%s*"%s.timeline_prefix):
        s.make_timeline()
    if not s.color:
        s.cuts = tuple(extract.cuts(s.timeline_prefix))
        s.color = tuple(extract.average_color(s.timeline_prefix))
        s.save()

    s.file.selected = True
    s.file.save()
    s.file.item.update_timeline()
    #make sure all derivatives exist
    s.extract_derivatives()

    #update clips
    for c in s.file.item.clips.all():
        c.update_calculated_values()
        c.save()

class Command(BaseCommand):
    """
    """
    help = 'update static files'
    args = ''

    def handle(self, **options):
        for root, folders, files in os.walk(os.path.join(settings.MEDIA_ROOT, 'files')):
            for f in files:
                f = os.path.join(root, f)
                profile, ext = os.path.splitext(os.path.basename(f))
                if ext in ('.webm', '.mp4'):
                    oshash = os.path.dirname(f)[-19:].replace('/', '')
                    format = ext[1:]
                    if profile.endswith('p'):
                        profile = profile[:-1]
                    resolution = int(profile)
                    qs = models.Stream.objects.filter(file__oshash=oshash, format=format, resolution=resolution)
                    if qs.count() == 0:
                        print 'add', f
                        print oshash, resolution, format
                        qs = models.File.objects.filter(oshash=oshash)
                        if qs.count() == 1:
                            stream = models.Stream()
                            stream.file = qs[0]
                            stream.resolution = resolution
                            stream.format = format
                            stream.video.name = f[len(settings.MEDIA_ROOT)+1:]
                            stream.available = True
                            stream.save()
                            if not stream.file.info:
                                stream.file.info = stream.info
                                stream.file.save()
        #link streams
        resolution = settings.CONFIG['video']['resolutions'][0]
        format = settings.CONFIG['video']['formats'][0]
        for s in models.Stream.objects.exclude(format=format, resolution=resolution).filter(source=None):
            s.source = models.Stream.objects.get(file=s.file, resolution=resolution, format=format)
            s.save()
        print "update streams"
        for s in models.Stream.objects.filter(source=None):
            update_stream.delay(s.id)
