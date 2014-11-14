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
                ('fdate', models.DateField(verbose_name=b'From Date')),
                ('tdate', models.DateField(verbose_name=b'To Date')),
                ('user', models.ForeignKey(related_name=b'activities', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ActivityWeeklyDescription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('week', models.CharField(default=1, max_length=1, verbose_name=b'Week', choices=[(b'1', b'1st Week'), (b'2', b'2nd Week'), (b'3', b'3rd Week'), (b'4', b'4th Week')])),
                ('description', models.CharField(max_length=255, verbose_name=b'Description')),
                ('activity', models.ForeignKey(related_name=b'description', verbose_name=b'Activity', to='board.Activity')),
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
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BeneficiaryGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name=b'Group Name')),
                ('user', models.ForeignKey(related_name=b'beneficiaryGroup', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='beneficiary',
            name='group',
            field=models.ManyToManyField(related_name=b'beneficiaries', to='board.BeneficiaryGroup', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='beneficiary',
            name='user',
            field=models.ForeignKey(related_name=b'beneficiaries', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='activityweeklydescription',
            name='beneficiaries',
            field=models.ManyToManyField(related_name=b'activityWeek', to='board.Beneficiary', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='activityweeklydescription',
            unique_together=set([('activity', 'week')]),
        ),
    ]
