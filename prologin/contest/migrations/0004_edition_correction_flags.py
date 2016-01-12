# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0003_fix_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='edition',
            name='qualification_corrected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='edition',
            name='semifinal_corrected',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='edition',
            name='final_corrected',
            field=models.BooleanField(default=False),
        ),
    ]
