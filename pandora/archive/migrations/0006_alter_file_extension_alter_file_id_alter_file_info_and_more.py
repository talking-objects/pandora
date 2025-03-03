# Generated by Django 4.2.3 on 2023-07-27 21:24

import django.core.serializers.json
from django.db import migrations, models
import oxdjango.fields


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0005_auto_20180804_1554'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='extension',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='file',
            name='info',
            field=oxdjango.fields.JSONField(default=dict, editable=False, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='file',
            name='language',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='part',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='part_title',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='path',
            field=models.CharField(default='', max_length=2048),
        ),
        migrations.AlterField(
            model_name='file',
            name='sort_path',
            field=models.CharField(default='', max_length=2048),
        ),
        migrations.AlterField(
            model_name='file',
            name='type',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='file',
            name='version',
            field=models.CharField(default='', max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='frame',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='instance',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='stream',
            name='error',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AlterField(
            model_name='stream',
            name='format',
            field=models.CharField(default='webm', max_length=255),
        ),
        migrations.AlterField(
            model_name='stream',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='stream',
            name='info',
            field=oxdjango.fields.JSONField(default=dict, editable=False, encoder=django.core.serializers.json.DjangoJSONEncoder),
        ),
        migrations.AlterField(
            model_name='volume',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
