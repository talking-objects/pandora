# Generated by Django 4.2.3 on 2023-07-27 21:28

import django.core.serializers.json
from django.db import migrations, models
import itemlist.models
import oxdjango.fields


class Migration(migrations.Migration):

    dependencies = [
        ('itemlist', '0003_jsonfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='list',
            name='description',
            field=models.TextField(default=''),
        ),
        migrations.AlterField(
            model_name='list',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='list',
            name='poster_frames',
            field=oxdjango.fields.JSONField(default=list, editable=False, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='list',
            name='query',
            field=oxdjango.fields.JSONField(default=itemlist.models.default_query, editable=False, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='list',
            name='sort',
            field=oxdjango.fields.JSONField(default=itemlist.models.get_listsort, editable=False, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='list',
            name='status',
            field=models.CharField(default='private', max_length=20),
        ),
        migrations.AlterField(
            model_name='list',
            name='type',
            field=models.CharField(default='static', max_length=255),
        ),
        migrations.AlterField(
            model_name='listitem',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='position',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
