# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('board', '0002_auto_20141019_2200'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='beneficiary',
            name='activity',
        ),
    ]
