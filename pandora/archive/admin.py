# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
from __future__ import division, print_function, absolute_import

from django.contrib import admin

from . import models


class FileAdmin(admin.ModelAdmin):
    search_fields = ['path', 'oshash', 'video_codec']
    list_display = ['available', 'wanted', 'selected', '__str__', 'public_id']
    list_display_links = ('__str__', )

    def public_id(self, obj):
        return '%s' % (obj.item.public_id)


admin.site.register(models.File, FileAdmin)


class InstanceAdmin(admin.ModelAdmin):
    search_fields = ['path', 'volume__name', 'file__oshash']

admin.site.register(models.Instance, InstanceAdmin)
