# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from prologin.utils import upload_path
import prologin.models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sponsor',
            fields=[
                ('address', models.TextField(blank=True, verbose_name='Address')),
                ('city', models.CharField(blank=True, max_length=64, verbose_name='City')),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('contact_first_name', models.CharField(blank=True, max_length=64)),
                ('contact_gender', prologin.models.GenderField(blank=True, null=True, verbose_name='Gender', choices=[(None, 'Prefer not to tell'), (0, 'Male'), (1, 'Female')])),
                ('contact_last_name', models.CharField(blank=True, max_length=64)),
                ('contact_phone_desk', models.CharField(blank=True, max_length=16)),
                ('contact_phone_fax', models.CharField(blank=True, max_length=16)),
                ('contact_phone_mobile', models.CharField(blank=True, max_length=16)),
                ('contact_position', models.CharField(blank=True, max_length=128)),
                ('country', models.CharField(blank=True, max_length=64, verbose_name='Country')),
                ('description', models.TextField(blank=True)),
                ('comment', models.TextField(blank=True)),
                ('editions', models.ManyToManyField(blank=True, to='contest.Edition')),
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('logo', models.ImageField(blank=True, upload_to=upload_path('sponsor'))),
                ('name', models.CharField(max_length=255, db_index=True)),
                ('postal_code', models.CharField(blank=True, max_length=32, verbose_name='Postal code')),
                ('site', models.URLField(blank=True)),
            ],
        ),
    ]
