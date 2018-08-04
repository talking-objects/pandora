# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-08-04 15:54
from __future__ import unicode_literals

import django.core.serializers.json
from django.db import migrations, models
import oxdjango.fields


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0004_jsonfield'),
    ]

    operations = [
        migrations.AddField(
            model_name='stream',
            name='flags',
            field=oxdjango.fields.JSONField(default=dict, editable=False, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
    ]
