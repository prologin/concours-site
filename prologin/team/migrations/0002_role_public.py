# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-04-30 19:21
from __future__ import unicode_literals

from django.db import migrations, models
import prologin.models
import team.models


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='role',
            name='public',
            field=models.BooleanField(default=True, help_text='Listed on the public team pages'),
        ),
    ]