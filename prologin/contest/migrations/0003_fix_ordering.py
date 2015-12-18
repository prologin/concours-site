# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0002_add_assignation_fields'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contestantcorrection',
            options={'ordering': ('-date_created',), 'get_latest_by': '-date_created'},
        ),
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ('date_begin',)},
        ),
        migrations.RenameField(
            model_name='contestantcorrection',
            old_name='date_added',
            new_name='date_created',
        ),
        migrations.AlterField(
            model_name='contestantcorrection',
            name='date_created',
            field=models.DateTimeField(default=django.utils.timezone.now, db_index=True),
        ),
    ]
