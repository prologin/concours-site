# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('team', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='role',
            options={'verbose_name': 'Role', 'verbose_name_plural': 'Roles', 'ordering': ('-significance',)},
        ),
        migrations.AlterModelOptions(
            name='teammember',
            options={'verbose_name': 'Team member', 'verbose_name_plural': 'Team members', 'ordering': ['-role__significance', 'user__username']},
        ),
    ]
