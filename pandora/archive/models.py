# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division

import os.path
import re
import time

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from ox.django import fields
import ox
from ox.normalize import canonicalTitle
import chardet

from item import utils
from item.models import Item
from person.models import get_name_sort


class File(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    verified = models.BooleanField(default=False)

    oshash = models.CharField(max_length=16, unique=True)
    item = models.ForeignKey(Item, related_name='files')

    name = models.CharField(max_length=2048, default="") # canoncial path/file
    folder = models.CharField(max_length=2048, default="") # canoncial path/file
    sort_name = models.CharField(max_length=2048, default="") # sort name

    type = models.CharField(default="", max_length=255)
    part = models.IntegerField(null=True)
    version = models.CharField(default="", max_length=255) # sort path/file name
    language = models.CharField(default="", max_length=8)

    season = models.IntegerField(default=-1)
    episode = models.IntegerField(default=-1)

    size = models.BigIntegerField(default=0)
    duration = models.BigIntegerField(null=True)

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
        self.name= self.get_name()
        self.folder = self.get_folder()
        if self.name and not self.sort_name:
            self.sort_name = utils.sort_string(canonicalTitle(self.name))
        if self.info:
            for key in ('duration', 'size'):
                setattr(self, key, self.info.get(key, 0))

            if 'video' in self.info and self.info['video'] and \
               'width' in self.info['video'][0]:
                video = self.info['video'][0]
                self.video_codec = video['codec']
                self.width = video['width']
                self.height = video['height']
                self.framerate = video['framerate']
                if 'display_aspect_ratio' in video:
                    self.display_aspect_ratio = video['display_aspect_ratio']
                else:
                    self.display_aspect_ratio = "%s:%s" % (self.width, self.height)
                self.is_video = True
                self.is_audio = False
                if self.name.endswith('.jpg') or \
                   self.name.endswith('.png') or \
                   self.duration == 0.04:
                    self.is_video = False
            else:
                self.is_video = False
                self.display_aspect_ratio = "4:3"
                self.width = '320'
                self.height = '240'
            if 'audio' in self.info and self.info['audio']:
                audio = self.info['audio'][0]
                self.audio_codec = audio['codec']
                self.samplerate = audio.get('samplerate', 0)
                self.channels = audio.get('channels', 0)

                if not self.is_video:
                    self.is_audio = True
            else:
                self.is_audio = False

            if self.framerate:
                self.pixels = int(self.width * self.height * float(utils.parse_decimal(self.framerate)) * self.duration)

        else:
            self.is_video = os.path.splitext(self.name)[-1] in ('.avi', '.mkv', '.dv', '.ogv', '.mpeg', '.mov')
            self.is_audio = os.path.splitext(self.name)[-1] in ('.mp3', '.wav', '.ogg', '.flac')
            self.is_subtitle= os.path.splitext(self.name)[-1] in ('.srt', '.sub', '.idx')

        if not self.is_audio and not self.is_video and self.name.endswith('.srt'):
            self.is_subtitle = True

        if self.name and self.name.lower().startswith('extras/'):
            self.is_extra = True
            self.is_main = False
        elif self.name and self.name.lower().startswith('versions/'):
            self.is_version = True
            self.is_main = False
        else:
            self.is_extra = False
            self.is_main = True

        self.part = self.get_part()
        self.type = self.get_type()

        if self.type not in ('audio', 'video'):
            self.duration = None
        super(File, self).save(*args, **kwargs)

    #upload and data handling
    video = models.FileField(null=True, blank=True,
                        upload_to=lambda f, x: f.path(settings.VIDEO_PROFILE))
    data = models.FileField(null=True, blank=True,
                        upload_to=lambda f, x: f.path('data.bin'))

    def path(self, name):
        h = self.oshash
        return os.path.join('files', h[:2], h[2:4], h[4:6], h[6:], name)

    def contents(self):
        if self.data != None:
            self.data.seek(0)
            return self.data.read()
        return None

    def srt(self):

        def _detectEncoding(fp):
            bomDict={ # bytepattern : name
                      (0x00, 0x00, 0xFE, 0xFF): "utf_32_be",
                      (0xFF, 0xFE, 0x00, 0x00): "utf_32_le",
                      (0xFE, 0xFF, None, None): "utf_16_be",
                      (0xFF, 0xFE, None, None): "utf_16_le",
                      (0xEF, 0xBB, 0xBF, None): "utf_8",
                    }

            # go to beginning of file and get the first 4 bytes
            oldFP = fp.tell()
            fp.seek(0)
            (byte1, byte2, byte3, byte4) = tuple(map(ord, fp.read(4)))

            # try bom detection using 4 bytes, 3 bytes, or 2 bytes
            bomDetection = bomDict.get((byte1, byte2, byte3, byte4))
            if not bomDetection:
                bomDetection = bomDict.get((byte1, byte2, byte3, None))
                if not bomDetection:
                    bomDetection = bomDict.get((byte1, byte2, None, None))

            ## if BOM detected, we're done :-)
            fp.seek(oldFP)
            if bomDetection:
                return bomDetection

            encoding = 'latin-1'
            #more character detecting magick using http://chardet.feedparser.org/
            fp.seek(0)
            rawdata = fp.read()
            encoding = chardet.detect(rawdata)['encoding']
            fp.seek(oldFP)
            return encoding

        def parseTime(t):
            return ox.time2ms(t.replace(',', '.')) / 1000

        srt = []

        f = open(self.data.path)
        encoding = _detectEncoding(f)
        data = f.read()
        f.close()
        data = data.replace('\r\n', '\n')
        try:
            data = unicode(data, encoding)
        except:
            try:
                data = unicode(data, 'latin-1')
            except:
                print "failed to detect encoding, giving up"
                return srt

        srts = re.compile('(\d\d:\d\d:\d\d[,.]\d\d\d)\s*-->\s*(\d\d:\d\d:\d\d[,.]\d\d\d)\s*(.+?)\n\n', re.DOTALL)
        i = 0
        for s in srts.findall(data):
            _s = {'id': str(i),
                  'in': parseTime(s[0]), 'out': parseTime(s[1]), 'value': s[2].strip()}
            srt.append(_s)
            i += 1
        return srt

    def editable(self, user):
        #FIXME: check that user has instance of this file
        return True

    def save_chunk(self, chunk, chunk_id=-1):
        if not self.available:
            if not self.video:
                self.video.save(settings.VIDEO_PROFILE, chunk)
            else:
                f = open(self.video.path, 'a')
                #FIXME: should check that chunk_id/offset is right
                f.write(chunk.read())
                f.close()
            return True
        return False

    def json(self, keys=None, user=None):
        resolution = (self.width, self.height)
        if resolution == (0, 0):
            resolution = None
        duration = self.duration
        if self.get_type() != 'video':
            duration = None
        data = {
            'available': self.available,
            'duration': duration,
            'framerate': self.framerate,
            'height': self.height,
            'width': self.width,
            'resolution': resolution,
            'oshash': self.oshash,
            'samplerate': self.samplerate,
            'video_codec': self.video_codec,
            'audio_codec': self.audio_codec,
            'name': self.name,
            'size': self.size,
            'info': self.info,
            'users': list(set([i.volume.user.username for i in self.instances.all()])),
            'instances': [i.json() for i in self.instances.all()],
            'folder': self.get_folder(),
            'type': self.get_type(),
            'is_main': self.is_main,
            'part': self.get_part()
        }
        if keys:
            for k in data.keys():
                if k not in keys:
                    del data[k]
        return data

    def get_part(self):
        if not self.is_extra:
            files = list(self.item.files.filter(type=self.type,
                                                is_main=self.is_main).order_by('sort_name'))
            if self in files:
                return files.index(self) + 1
        return None

    def get_type(self):
        if self.is_video:
            return 'video'
        if self.is_audio:
            return 'audio'
        if self.is_subtitle or os.path.splitext(self.name)[-1] in ('.sub', '.idx'):
            return 'subtitle'
        return 'unknown'

    def get_folder(self):
        name = os.path.splitext(self.get_name())[0]
        if self.item:
            if settings.USE_IMDB:
                director = self.item.get('director', ['Unknown Director'])
                director = map(get_name_sort, director)
                director = '; '.join(director)
                director = re.sub(r'[:\\/]', '_', director)
                name = os.path.join(director, name)
            year = self.item.get('year', None)
            if year:
                name += u' (%s)' % year
            name = os.path.join(name[0].upper(), name)
            return name
        return ''

    def get_name(self):
        if self.item:
            name = self.item.get('title', 'Untitled')
            name = re.sub(r'[:\\/]', '_', name)
        if not name:
            name = 'Untitled'
        if self.instances.count() > 0:
            ext = os.path.splitext(self.instances.all()[0].name)[-1]
        else:
            ext = '.unknown'
        return name + ext

class Volume(models.Model):

    class Meta:
        unique_together = ("user", "name")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, related_name='volumes')
    name = models.CharField(max_length=1024)

    def __unicode__(self):
        return u"%s's %s"% (self.user, self.name)


class Instance(models.Model):

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
    def itemId(self):
        return File.objects.get(oshash=self.oshash).itemId

    def json(self):
        return {
            'user': self.volume.user.username,
            'volume': self.volume.name,
            'folder': self.folder,
            'name': self.name
        }

def frame_path(frame, name):
    ext = os.path.splitext(name)[-1]
    name = "%s%s" % (frame.position, ext)
    return frame.file.path(name)


class Frame(models.Model):

    class Meta:
        unique_together = ("file", "position")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    file = models.ForeignKey(File, related_name="frames")
    position = models.FloatField()
    frame = models.ImageField(default=None, null=True, upload_to=frame_path)

    '''
    def save(self, *args, **kwargs):
        name = "%d.jpg" % self.position
        if file.name != name:
            #FIXME: frame path should be renamed on save to match current position
        super(Frame, self).save(*args, **kwargs)
    '''

    def __unicode__(self):
        return u'%s/%s' % (self.file, self.position)
