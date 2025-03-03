# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-19 15:37
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import itemlist.models
import oxdjango.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('item', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='List',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=255)),
                ('status', models.CharField(default=b'private', max_length=20)),
                ('query', oxdjango.fields.DictField(default={b'static': True})),
                ('type', models.CharField(default=b'static', max_length=255)),
                ('description', models.TextField(default=b'')),
                ('icon', models.ImageField(blank=True, default=None, upload_to=itemlist.models.get_icon_path)),
                ('view', models.TextField(default=itemlist.models.get_listview)),
                ('sort', oxdjango.fields.TupleField(default=itemlist.models.get_listsort, editable=False)),
                ('poster_frames', oxdjango.fields.TupleField(default=[], editable=False)),
                ('numberofitems', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='ListItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('index', models.IntegerField(default=0)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='item.Item')),
                ('list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='itemlist.List')),
            ],
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section', models.CharField(max_length=255)),
                ('position', models.IntegerField(default=0)),
                ('list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='position', to='itemlist.List')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='list',
            name='items',
            field=models.ManyToManyField(related_name='lists', through='itemlist.ListItem', to='item.Item'),
        ),
        migrations.AddField(
            model_name='list',
            name='subscribed_users',
            field=models.ManyToManyField(related_name='subscribed_lists', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='list',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lists', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='position',
            unique_together=set([('user', 'list', 'section')]),
        ),
        migrations.AlterUniqueTogether(
            name='list',
            unique_together=set([('user', 'name')]),
        ),
    ]
