# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

import centers.models
import prologin.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Center',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('address', models.TextField(verbose_name='Address', blank=True)),
                ('postal_code', models.CharField(max_length=32, blank=True, verbose_name='Postal code')),
                ('city', models.CharField(max_length=64, blank=True, verbose_name='City')),
                ('country', models.CharField(max_length=64, blank=True, verbose_name='Country')),
                ('name', models.CharField(max_length=64)),
                ('type', prologin.models.EnumField(centers.models.Center.Type, choices=[(0, 'Center'), (1, 'Restaurant'), (2, 'Hotel'), (3, 'Pizzeria'), (4, 'Other')])),
                ('is_active', models.BooleanField(default=True)),
                ('lat', models.DecimalField(max_digits=16, default=0, decimal_places=6)),
                ('lng', models.DecimalField(max_digits=16, default=0, decimal_places=6)),
                ('comments', models.TextField(blank=True)),
            ],
            options={
                'ordering': ('type', 'name', 'city'),
            },
        ),
        migrations.CreateModel(
            name='Contact',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('contact_gender', prologin.models.GenderField(verbose_name='Gender', null=True, blank=True, choices=[(None, 'Prefer not to tell'), (0, 'Male'), (1, 'Female')])),
                ('contact_position', models.CharField(max_length=128, blank=True)),
                ('contact_first_name', models.CharField(max_length=64, blank=True)),
                ('contact_last_name', models.CharField(max_length=64, blank=True)),
                ('contact_phone_desk', models.CharField(max_length=16, blank=True)),
                ('contact_phone_mobile', models.CharField(max_length=16, blank=True)),
                ('contact_phone_fax', models.CharField(max_length=16, blank=True)),
                ('contact_email', models.EmailField(max_length=254, blank=True)),
                ('type', prologin.models.EnumField(centers.models.Contact.Type, db_index=True, choices=[(0, 'Manager'), (1, 'Contact')])),
                ('center', models.ForeignKey(related_name='contacts', to='centers.Center', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
