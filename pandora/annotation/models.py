# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, with_statement

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
import ox

from archive import extract
from clip.models import Clip

from item.utils import sort_string
import managers
import utils
from tasks import update_matching_events, update_matching_places



class Annotation(models.Model):
    objects = managers.AnnotationManager()

    #FIXME: here having a item,start index would be good
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User)
    item = models.ForeignKey('item.Item', related_name='annotations')
    clip = models.ForeignKey('clip.Clip', null=True, related_name='annotations')

    public_id = models.CharField(max_length=128, unique=True, null=True)
    #seconds
    start = models.FloatField(default=-1, db_index=True)
    end = models.FloatField(default=-1)

    layer = models.CharField(max_length=255, db_index=True)
    value = models.TextField()
    findvalue = models.TextField()
    sortvalue = models.CharField(max_length=1000, null=True, blank=True, db_index=True)

    def editable(self, user):
        if user.is_authenticated():
            if user.is_staff or \
               self.user == user or \
               user.groups.filter(id__in=self.groups.all()).count() > 0:
                return True
        return False

    def set_public_id(self):
        if self.id:
            public_id = Annotation.objects.filter(item=self.item, id__lt=self.id).count() + 1
            self.public_id = "%s/%s" % (self.item.itemId, ox.toAZ(public_id))
            Annotation.objects.filter(id=self.id).update(public_id=self.public_id)

    def get_layer(self):
        for layer in settings.CONFIG['layers']:
            if layer['id'] == self.layer:
                return layer
        return {}

    def save(self, *args, **kwargs):
        set_public_id = not self.id or not self.public_id
        layer = self.get_layer()
        if self.value:
            self.value = utils.cleanup_value(self.value, self.layer['type'])
            self.findvalue = ox.stripTags(self.value).strip()
            sortvalue = self.findvalue
            sortvalue = sort_string(sortvalue)
            if sortvalue:
                self.sortvalue = sortvalue[:1000]
            else:
                self.sortvalue = None
        else:
            self.sortvalue = None

        #no clip or update clip
        private = layer.get('private', False)
        if not private:
            if not self.clip or self.start != self.clip.start or self.end != self.clip.end:
                self.clip, created = Clip.get_or_create(self.item, self.start, self.end)

        super(Annotation, self).save(*args, **kwargs)
        if set_public_id:
            self.set_public_id()

        if self.clip:
            Clip.objects.filter(**{
                'id': self.clip.id,
                self.layer: False
            }).update(**{self.layer: True})

        #how expensive is this?
        #update_matching_events.delay(self.value)
        #update_matching_places.delay(self.value)

    def json(self, layer=False, keys=None):
        j = {
            'user': self.user.username,
        }
        for field in ('id', 'in', 'out', 'value', 'created', 'modified'):
            j[field] = getattr(self, {
                'duration': 'clip__duration',
                'hue': 'clip__hue',
                'id': 'public_id',
                'in': 'start',
                'lightness': 'clip__lightness',
                'out': 'end',
                'saturation': 'clip__saturation',
                'volume': 'clip__volume',
            }.get(field, field))
        if layer or (keys and 'layer' in keys):
            j['layer'] = self.layer
        if keys:
            _j = {}
            for key in keys:
                if key in j:
                    _j[key] = j[key]
            j = _j
            if 'videoRatio' in keys:
                streams = self.item.streams()
                if streams:
                    j['videoRatio'] = streams[0].aspect_ratio
        return j

    def __unicode__(self):
        return u"%s %s-%s" %(self.public_id, self.start, self.end)

