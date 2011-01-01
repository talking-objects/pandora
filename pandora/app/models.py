# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from django.db import models


class Page(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=1024, unique=True)
    body = models.TextField(blank=True)

    def __unicode__(self):
        return self.name


class SiteSettings(models.Model):
    key = models.CharField(max_length=1024, unique=True)
    value = models.TextField(blank=True)

    def __unicode__(self):
        return self.key
