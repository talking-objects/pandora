# -*- coding: utf-8 -*-

import os
import re
import subprocess
from glob import glob

from django.db import models
from django.db.models import Max
from django.contrib.auth import get_user_model
from django.conf import settings
from oxdjango.fields import JSONField

import ox

from archive import extract
from user.utils import update_groups
from user.models import Group

from . import managers

User = get_user_model()

def get_path(f, x): return f.path(x)
def get_icon_path(f, x): return get_path(f, 'icon.jpg')
def get_listview(): return settings.CONFIG['user']['ui']['listView']
def get_listsort(): return tuple(settings.CONFIG['user']['ui']['listSort'])

def default_query():
    return {"static": True}

class List(models.Model):

    class Meta:
        unique_together = ("user", "name")

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, related_name='lists', on_delete=models.CASCADE)
    groups = models.ManyToManyField(Group, blank=True, related_name='lists')
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='private')
    _status = ['private', 'public', 'featured']
    query = JSONField(default=default_query, editable=False)
    type = models.CharField(max_length=255, default='static')
    description = models.TextField(default='')

    icon = models.ImageField(default=None, blank=True, upload_to=get_icon_path)

    view = models.TextField(default=get_listview)
    sort = JSONField(default=get_listsort, editable=False)

    poster_frames = JSONField(default=list, editable=False)

    #is through table still required?
    items = models.ManyToManyField('item.Item', related_name='lists',
                                                through='ListItem')

    numberofitems = models.IntegerField(default=0)
    subscribed_users = models.ManyToManyField(User, related_name='subscribed_lists')

    objects = managers.ListManager()

    def save(self, *args, **kwargs):
        if self.query.get('static', False):
            self.type = 'static'
        else:
            self.type = 'smart'
        if self.id:
            self.numberofitems = self.get_numberofitems(self.user)
        super(List, self).save(*args, **kwargs)

    @classmethod
    def get(cls, id):
        id = id.split(':')
        username = id[0]
        listname = ":".join(id[1:])
        return cls.objects.get(user__username=username, name=listname)

    def get_items(self, user=None):
        if self.query.get('static', False):
            return self.items
        from item.models import Item
        return Item.objects.find({'query': self.query}, user)


    def get_numberofitems(self, user=None):
        return self.get_items(user).count()

    def add(self, item):
        q = self.items.filter(id=item.id)
        if q.count() == 0:
            l = ListItem()
            l.list = self
            l.item = item
            l.index = ListItem.objects.filter(list=self).aggregate(Max('index'))['index__max']
            if l.index == None:
                l.index = 0
            else:
                l.index += 1
            l.save()

    def remove(self, item=None, items=None):
        if item:
            ListItem.objects.all().filter(item=item, list=self).delete()
        if items:
            ListItem.objects.all().filter(item__public_id__in=items, list=self).delete()

    def __str__(self):
        return self.get_id()

    def get_id(self):
        return '%s:%s' % (self.user.username, self.name)

    def accessible(self, user):
        return self.user == user or self.status in ('public', 'featured')

    def editable(self, user):
        if not user or user.is_anonymous:
            return False
        if self.user == user or \
           self.groups.filter(id__in=user.groups.all()).count() > 0 or \
           user.is_staff or \
           user.profile.capability('canEditFeaturedLists'):
            return True
        return False

    def edit(self, data, user):
        if 'groups' in data:
            groups = data.pop('groups')
            update_groups(self, groups)
        for key in data:
            if key == 'query' and not data['query']:
                setattr(self, key, {"static": True})
            elif key == 'query' and isinstance(data[key], dict):
                setattr(self, key, data[key])
            elif key == 'type':
                if data[key] == 'static':
                    self.query = {"static": True}
                    self.type = 'static'
                else:
                    self.type = 'smart'
                    if self.query.get('static', False):
                         self.query = {}
            elif key == 'status':
                value = data[key]
                if value not in self._status:
                    value = self._status[0]
                if value == 'private':
                    for user in self.subscribed_users.all():
                        self.subscribed_users.remove(user)
                    qs = Position.objects.filter(user=user, list=self)
                    if qs.count() > 1:
                        pos = qs[0]
                        pos.section = 'personal'
                        pos.save()
                elif value == 'featured':
                    if user.profile.capability('canEditFeaturedLists'):
                        pos, created = Position.objects.get_or_create(list=self, user=user,
                                                                             section='featured')
                        if created:
                            qs = Position.objects.filter(user=user, section='featured')
                            pos.position = qs.aggregate(Max('position'))['position__max'] + 1
                            pos.save()
                        Position.objects.filter(list=self).exclude(id=pos.id).delete()
                    else:
                        value = self.status
                elif self.status == 'featured' and value == 'public':
                    Position.objects.filter(list=self).delete()
                    pos, created = Position.objects.get_or_create(list=self,
                                                  user=self.user, section='personal')
                    qs = Position.objects.filter(user=self.user, section='personal')
                    pos.position = qs.aggregate(Max('position'))['position__max'] + 1
                    pos.save()
                    for u in self.subscribed_users.all():
                        pos, created = Position.objects.get_or_create(list=self, user=u,
                                                                             section='public')
                        qs = Position.objects.filter(user=u, section='public')
                        pos.position = qs.aggregate(Max('position'))['position__max'] + 1
                        pos.save()

                self.status = value
            elif key == 'name':
                data['name'] = re.sub(' \[\d+\]$', '', data['name']).strip()
                if not data['name']:
                    data['name'] = "Untitled"
                name = data['name']
                num = 1
                while List.objects.filter(name=name, user=self.user).exclude(id=self.id).count()>0:
                    num += 1
                    name = data['name'] + ' [%d]' % num
                self.name = name
            elif key == 'description':
                self.description = ox.sanitize_html(data['description'])

        if 'position' in data:
            pos, created = Position.objects.get_or_create(list=self, user=user)
            pos.position = data['position']
            pos.section = 'featured'
            if self.status == 'private':
                pos.section = 'personal'
            pos.save()
        if 'posterFrames' in data:
            self.poster_frames = tuple(data['posterFrames'])
        if 'view' in data:
            self.view = data['view']
        if 'sort' in data:
            self.sort = tuple(data['sort'])
        self.save()
        if 'posterFrames' in data:
            self.update_icon()

    def json(self, keys=None, user=None):
        if not keys:
            keys = [
                'description',
                'editable',
                'groups',
                'id',
                'name',
                'posterFrames',
                'query',
                'status',
                'subscribed',
                'type',
                'user',
                'view',
            ]
        response = {}
        for key in keys:
            if key == 'items':
                response[key] = self.get_numberofitems(user)
            elif key == 'id':
                response[key] = self.get_id()
            elif key == 'user':
                response[key] = self.user.username
            elif key == 'groups':
                response[key] = [g.name for g in self.groups.all()]
            elif key == 'editable':
                response[key] = self.editable(user)
            elif key == 'query':
                if not self.query.get('static', False):
                    response[key] = self.query
            elif key == 'subscribers':
                response[key] = self.subscribed_users.all().count()
            elif key == 'subscribed':
                if user and not user.is_anonymous:
                    response[key] = self.subscribed_users.filter(id=user.id).exists()
            else:
                response[key] = getattr(self, {
                    'posterFrames': 'poster_frames'
                }.get(key, key))
        return response

    def path(self, name=''):
        h = "%07d" % self.id
        return os.path.join('lists', h[:2], h[2:4], h[4:6], h[6:], name)

    def update_icon(self):
        frames = []
        if not self.poster_frames:
            items = self.get_items(self.user).filter(rendered=True)
            if items.count():
                poster_frames = []
                for i in range(0, items.count(), max(1, int(items.count()/4))):
                    poster_frames.append({
                        'item': items[int(i)].public_id,
                        'position': items[int(i)].poster_frame
                    })
                self.poster_frames = tuple(poster_frames)
                self.save()
        for i in self.poster_frames:
            from item.models import Item
            if 'item' in i:
                qs = Item.objects.filter(public_id=i['item'])
                if qs.count() > 0:
                    if i.get('position'):
                        frame = qs[0].frame(i['position'])
                        if frame:
                            frames.append(frame)
        self.icon.name = self.path('icon.jpg')
        icon = self.icon.path
        if frames:
            while len(frames) < 4:
                frames += frames
            folder = os.path.dirname(icon)
            ox.makedirs(folder)
            for f in glob("%s/icon*.jpg" % folder):
                os.unlink(f)
            cmd = [
                settings.LIST_ICON,
                '-f', ','.join(frames),
                '-o', icon
            ]
            p = subprocess.Popen(cmd, close_fds=True)
            p.wait()
            self.save()

    def get_icon(self, size=16):
        path = self.path('icon%d.jpg' % size)
        path = os.path.join(settings.MEDIA_ROOT, path)
        if not os.path.exists(path):
            folder = os.path.dirname(path)
            ox.makedirs(folder)
            if self.icon and os.path.exists(self.icon.path):
                source = self.icon.path
                max_size = min(self.icon.width, self.icon.height)
            else:
                source = os.path.join(settings.STATIC_ROOT, 'jpg/list256.jpg')
                max_size = 256
            if size < max_size:
                extract.resize_image(source, path, size=size)
            else:
                path = source
        return path

class ListItem(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    list = models.ForeignKey(List, on_delete=models.CASCADE)
    index = models.IntegerField(default=0)
    item = models.ForeignKey('item.Item', on_delete=models.CASCADE)

    def __str__(self):
        return '%s in %s' % (self.item, self.list)


class Position(models.Model):

    class Meta:
        unique_together = ("user", "list", "section")

    list = models.ForeignKey(List, related_name='position', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    section = models.CharField(max_length=255)
    position = models.IntegerField(default=0)

    def __str__(self):
        return '%s/%s/%s' % (self.section, self.position, self.list)

