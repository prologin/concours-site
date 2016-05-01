# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import prologin.models
import contest.models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='contestant',
            old_name='assigned_event',
            new_name='assignation_semifinal_event',
        ),
        migrations.RenameField(
            model_name='contestant',
            old_name='event_wishes',
            new_name='assignation_semifinal_wishes',
        ),
        migrations.AddField(
            model_name='contestant',
            name='assignation_semifinal',
            field=prologin.models.EnumField(contest.models.Assignation, default=0, choices=[(0, 'Not assigned'), (1, 'Ruled out'), (2, 'Assigned')], verbose_name='Regional event assignation status'),
        ),
        migrations.AddField(
            model_name='contestant',
            name='assignation_final',
            field=prologin.models.EnumField(contest.models.Assignation, default=0, choices=[(0, 'Not assigned'), (1, 'Ruled out'), (2, 'Assigned')], verbose_name='Final assignation status'),
        ),
    ]
