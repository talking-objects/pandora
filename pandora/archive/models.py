# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from datetime import datetime
import os.path
import random
import re
from decimal import Decimal
import time

from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.utils import simplejson as json
from django.conf import settings

from oxdjango import fields
import ox
from ox import stripTags
from ox.normalize import canonicalTitle, canonicalName
from firefogg import Firefogg

from backend import utils
from backend import extract
from pandora.backend.models import Movie

import extract


def parse_decimal(string):
    string = string.replace(':', '/')
    if '/' not in string:
        string = '%s/1' % string
    d = string.split('/')
    return Decimal(d[0]) / Decimal(d[1])

class File(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    verified = models.BooleanField(default=False)

    oshash = models.CharField(max_length=16, unique=True)
    movie = models.ForeignKey(Movie, related_name='files')

    name = models.CharField(max_length=2048, default="") # canoncial path/file
    sort_name = models.CharField(max_length=2048, default="") # sort path/file name

    part = models.CharField(default="", max_length=255)
    version = models.CharField(default="", max_length=255) # sort path/file name
    language = models.CharField(default="", max_length=8)

    season = models.IntegerField(default=-1)
    episode = models.IntegerField(default=-1)

    size = models.BigIntegerField(default=0)
    duration = models.IntegerField(default=0)

    info = fields.DictField(default={})

    video_codec = models.CharField(max_length=255)
    pixel_format = models.CharField(max_length=255)
    display_aspect_ratio = models.CharField(max_length=255)
    width = models.IntegerField(default = 0)
    height = models.IntegerField(default = 0)
    framerate = models.CharField(max_length=255)

    audio_codec = models.CharField(max_length=255)
    channels = models.IntegerField(default=0)
    samplerate = models.IntegerField(default=0)

    bits_per_pixel = models.FloatField(default=-1)
    pixels = models.BigIntegerField(default=0)

    #This is true if derivative is available or subtitles where uploaded
    available = models.BooleanField(default = False)

    is_audio = models.BooleanField(default=False)
    is_video = models.BooleanField(default=False)
    is_extra = models.BooleanField(default=False)
    is_main = models.BooleanField(default=False)
    is_subtitle = models.BooleanField(default=False)
    is_version = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.name and not self.sort_name:
            self.sort_name = canonicalTitle(self.name)
        if self.info:
            for key in ('duration', 'size'):
                setattr(self, key, self.info.get(key, 0))

            if 'video' in self.info and self.info['video']:
                self.video_codec = self.info['video'][0]['codec']
                self.width = self.info['video'][0]['width']
                self.height = self.info['video'][0]['height']
                self.framerate = self.info['video'][0]['framerate']
                if 'display_aspect_ratio' in self.info['video'][0]:
                    self.display_aspect_ratio = self.info['video'][0]['display_aspect_ratio']
                else:
                    self.display_aspect_ratio = "%s:%s" % (self.width, self.height)
                self.is_video = True
                self.is_audio = False
            else:
                self.is_video = False
            if 'audio' in self.info and self.info['audio']:
                self.audio_codec = self.info['audio'][0]['codec']
                self.samplerate = self.info['audio'][0]['samplerate']
                self.channels = self.info['audio'][0]['channels']

                if not self.is_video:
                    self.is_audio = True
            else:
                self.is_audio = False

            if self.framerate:
                self.pixels = int(self.width * self.height * float(parse_decimal(self.framerate)) * self.duration)

        if not self.is_audio and not self.is_video and self.name.endswith('.srt'):
            self.is_subtitle = True

        if self.name and self.name.startswith('Extras/'):
            self.is_extra = True
            self.is_main = False
        else:
            self.is_extra = False
            self.is_main = True

        super(File, self).save(*args, **kwargs)

    def json(self):
        r = {}
        for k in self:
            r[k] = unicode(self[k])
        return r

    def contents(self):
        if self.contents_set.count() > 0:
            return self.contents_set.all()[0].data
        return None

class Volume(models.Model):
    class Meta:
        unique_together = ("user", "name")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, related_name='volumes')
    name = models.CharField(max_length=1024)

    def __unicode__(self):
        return u"%s's %s"% (self.user, self.name)

class FileInstance(models.Model):
    class Meta:
        unique_together = ("name", "folder", "volume")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    atime = models.IntegerField(default=lambda: int(time.time()), editable=False)
    ctime = models.IntegerField(default=lambda: int(time.time()), editable=False)
    mtime = models.IntegerField(default=lambda: int(time.time()), editable=False)

    name = models.CharField(max_length=2048)
    folder = models.CharField(max_length=255)

    file = models.ForeignKey(File, related_name='instances')
    volume = models.ForeignKey(Volume, related_name='files')

    def __unicode__(self):
        return u"%s's %s <%s>"% (self.volume.user, self.name, self.file.oshash)

    @property
    def movieId(self):
        return File.objects.get(oshash=self.oshash).movieId

def frame_path(f, name):
    ext = os.path.splitext(name)[-1]
    name = "%s%s" % (f.position, ext)
    h = f.file.oshash
    return os.path.join('frame', h[:2], h[2:4], h[4:6], name)

class Frame(models.Model):
    class Meta:
        unique_together = ("file", "position")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    file = models.ForeignKey(File, related_name="frames")
    position = models.FloatField()
    frame = models.ImageField(default=None, null=True, upload_to=frame_path)

    #FIXME: frame path should be renamed on save to match current position

    def __unicode__(self):
        return u'%s at %s' % (self.file, self.position)

def stream_path(f):
    h = f.file.oshash
    return os.path.join('stream', h[:2], h[2:4], h[4:6], h[6:], f.profile)

class Stream(models.Model):
    class Meta:
        unique_together = ("file", "profile")

    file = models.ForeignKey(File, related_name='streams')
    profile = models.CharField(max_length=255, default='96p.webm')
    video = models.FileField(default=None, blank=True, upload_to=lambda f, x: stream_path(f))
    source = models.ForeignKey('Stream', related_name='derivatives', default=None, null=True)
    available = models.BooleanField(default=False)

    def __unicode__(self):
        return self.video

    def extract_derivates(self):
        if settings.VIDEO_H264:
            profile = self.profile.replace('.webm', '.mp4')
            if Stream.objects.filter(profile=profile, source=self).count() == 0:
                derivate = Stream(file=self.file, source=self, profile=profile)
                derivate.video.name = self.video.name.replace(self.profile, profile)
                derivate.encode()

        for p in settings.VIDEO_DERIVATIVES:
            profile = p + '.webm'
            target = self.video.path.replace(self.profile, profile)
            if Stream.objects.filter(profile=profile, source=self).count() == 0:
                derivate = Stream(file=self.file, source=self, profile=profile)
                derivate.video.name = self.video.name.replace(self.profile, profile)
                derivate.encode()

            if settings.VIDEO_H264:
                profile = p + '.mp4'
                if Stream.objects.filter(profile=profile, source=self).count() == 0:
                    derivate = Stream(file=self.file, source=self, profile=profile)
                    derivate.video.name = self.video.name.replace(self.profile, profile)
                    derivate.encode()
        return True

    def encode(self):
        if self.source:
            video = self.source.video.path
            target = self.video.path
            profile = self.profile
            info = self.file.info
            if extract.stream(video, target, profile, info):
                self.available=True
                self.save()

    def editable(self, user):
        #FIXME: possibly needs user setting for stream
        return True

    def save_chunk(self, chunk, chunk_id=-1):
        if not self.available:
            if not self.video:
                self.video.save(self.profile, chunk)
            else:
                f = open(self.video.path, 'a')
                #FIXME: should check that chunk_id/offset is right
                f.write(chunk.read())
                f.close()
            return True
        return False

    def save(self, *args, **kwargs):
        if self.available and not self.file.available:
            self.file.available = True
            self.file.save()
        super(Stream, self).save(*args, **kwargs)

class FileContents(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    file = models.ForeignKey(File, related_name="contents_set")
    data = models.TextField(default=u'')

    def save(self, *args, **kwargs):
        if self.data and not self.file.available:
            self.file.available = True
            self.file.save()
        super(FileContents, self).save(*args, **kwargs)

