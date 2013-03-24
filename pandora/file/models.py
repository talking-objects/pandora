# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement
import os
import re
import subprocess
from urllib import quote

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_delete

import Image
import ox

import managers


class File(models.Model):

    class Meta:
        unique_together = ("user", "name", "extension")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    user = models.ForeignKey(User, related_name='files')
    name = models.CharField(max_length=255)
    extension = models.CharField(max_length=255)
    size = models.IntegerField(default=0)
    matches = models.IntegerField(default=0)
    ratio = models.FloatField(default=1)
    description = models.TextField(default="")
    oshash = models.CharField(max_length=16, unique=True, null=True)

    file = models.FileField(default=None, blank=True,null=True, upload_to=lambda f, x: f.path(x))

    objects = managers.FileManager()
    uploading = models.BooleanField(default = False)

    name_sort = models.CharField(max_length=255)
    description_sort = models.CharField(max_length=512)

    def save(self, *args, **kwargs):
        if not self.uploading:
            if self.file:
                self.size = self.file.size
                if self.extension == 'pdf' and not os.path.exists(self.thumbnail()):
                    self.make_thumbnail()

        self.name_sort = ox.sort_string(self.name or u'')[:255]
        self.description_sort = ox.sort_string(self.description or u'')[:512]

        super(File, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.get_id()

    @classmethod
    def get(cls, id):
        username, name, extension = cls.parse_id(id)
        return cls.objects.get(user__username=username, name=name, extension=extension)

    @classmethod
    def parse_id(cls, id):
        public_id = id.split(':')
        username = public_id[0]
        name = ":".join(public_id[1:])
        extension = name.split('.')
        name = '.'.join(extension[:-1])
        extension = extension[-1].lower()
        return username, name, extension

    def get_absolute_url(self):
        return '/files/%s' % quote(self.get_id())

    def get_id(self):
        return u'%s:%s.%s' % (self.user.username, self.name, self.extension)

    def editable(self, user):
        if not user or user.is_anonymous():
            return False
        if self.user == user or \
           user.is_staff or \
           user.get_profile().capability('canEditFiles') == True:
            return True
        return False

    def edit(self, data, user):
        for key in data:
            if key == 'name':
                data['name'] = re.sub(' \[\d+\]$', '', data['name']).strip()
                if not data['name']:
                    data['name'] = "Untitled"
                name = data['name']
                num = 1
                while File.objects.filter(name=name, user=self.user, extension=self.extension).exclude(id=self.id).count()>0:
                    num += 1
                    name = data['name'] + ' [%d]' % num
                self.name = name
            elif key == 'description':
                self.description = ox.sanitize_html(data['description'])

    def json(self, keys=None, user=None):
        if not keys:
             keys=[
                'description',
                'editable',
                'id',
                'name',
                'extension',
                'oshash',
                'size',
                'ratio',
                'user'
            ]
        response = {}
        _map = {
        }
        for key in keys:
            if key == 'id':
                response[key] = self.get_id()
            elif key == 'editable':
                response[key] = self.editable(user)
            elif key == 'user':
                response[key] = self.user.username
            elif hasattr(self, _map.get(key, key)):
                response[key] = getattr(self, _map.get(key,key))
        return response

    def path(self, name=''):
        h = "%07d" % self.id
        return os.path.join('uploads', h[:2], h[2:4], h[4:6], h[6:], name)

    def save_chunk(self, chunk, chunk_id=-1, done=False):
        if self.uploading:
            if not self.file:
                name = 'data.%s' % self.extension
                self.file.name = self.path(name)
                ox.makedirs(os.path.dirname(self.file.path))
                with open(self.file.path, 'w') as f:
                    f.write(chunk.read())
                self.save()
            else:
                with open(self.file.path, 'a') as f:
                    f.write(chunk.read())
            if done:
                self.uploading = False
                self.get_ratio()
                self.oshash = ox.oshash(self.file.path)
                self.save()
            return True
        return False

    def thumbnail(self):
        return '%s.jpg' % self.file.path

    def make_thumbnail(self, force=False):
        thumb = self.thumbnail()
        if not os.path.exists(thumb) or force:
            cmd = ['convert', '%s[0]' % self.file.path,
                '-background', 'white', '-flatten', '-resize', '256x256', thumb]
            p = subprocess.Popen(cmd)
            p.wait()

    def get_ratio(self):
        if self.extension == 'pdf':
            self.make_thumbnail()
            image = self.thumbnail()
        else:
            image = self.file.path
        try:
            size = Image.open(image).size
        except:
            size = [1,1]
        self.ratio = size[0] / size[1]



def delete_file(sender, **kwargs):
    t = kwargs['instance']
    if t.file:
        if t.extension == 'pdf':
            thumb = t.thumbnail()
            if os.path.exists(thumb):
                os.unlink(thumb)
        t.file.delete()
pre_delete.connect(delete_file, sender=File)

