# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-19 15:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('document', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('item', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='itemproperties',
            name='item',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='item.Item'),
        ),
        migrations.AddField(
            model_name='document',
            name='items',
            field=models.ManyToManyField(related_name='documents', through='document.ItemProperties', to='item.Item'),
        ),
        migrations.AddField(
            model_name='document',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='itemproperties',
            unique_together=set([('item', 'document')]),
        ),
        migrations.AlterUniqueTogether(
            name='document',
            unique_together=set([('user', 'name', 'extension')]),
        ),
    ]
