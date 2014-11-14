# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityweeklydescription',
            name='description',
            field=models.CharField(max_length=255, null=True, verbose_name=b'Description', blank=True),
        ),
    ]
