# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-10-27 12:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
        ('document', '0008_auto_20161026_1625'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='documents', to='auth.Group'),
        ),
    ]
