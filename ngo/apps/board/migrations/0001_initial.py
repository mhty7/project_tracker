# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activity_ty', models.CharField(default=1, max_length=1, verbose_name=b'Activity Type', choices=[(b'1', b'Outreach'), (b'2', b'Get-Together'), (b'3', b'Circle'), (b'4', b'Formative Talk'), (b'5', b'Basic Course'), (b'6', b'Excursion'), (b'7', b'Mentoring'), (b'8', b'Others')])),
                ('description', models.CharField(max_length=255, verbose_name=b'Description')),
                ('income', models.DecimalField(verbose_name=b'Income', max_digits=13, decimal_places=2)),
                ('fdate', models.DateField(verbose_name=b'From Date')),
                ('tdate', models.DateField(verbose_name=b'To Date')),
                ('staff_exp', models.DecimalField(verbose_name=b'Staff Expense', max_digits=13, decimal_places=2)),
                ('materials_exp', models.DecimalField(verbose_name=b'Material Expense', max_digits=13, decimal_places=2)),
                ('transp_exp', models.DecimalField(verbose_name=b'Transportation Expense', max_digits=13, decimal_places=2)),
                ('other_exp', models.DecimalField(verbose_name=b'Other expense', max_digits=13, decimal_places=2)),
                ('user', models.ForeignKey(related_name=b'activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Beneficiary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ty', models.CharField(default=1, max_length=1, verbose_name=b'Type', choices=[(b'1', b'direct'), (b'2', b'indirect')])),
                ('lname', models.CharField(max_length=50, verbose_name=b'Last Name')),
                ('fname', models.CharField(max_length=50, verbose_name=b'First Name')),
                ('activity', models.ManyToManyField(related_name=b'beneficiaries', to='board.Activity')),
                ('user', models.ForeignKey(related_name=b'beneficiaries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
