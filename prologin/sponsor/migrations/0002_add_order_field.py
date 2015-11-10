# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sponsor', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sponsor',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='sponsor',
            name='order',
            field=models.SmallIntegerField(editable=False, default=0, db_index=True),
        ),
    ]
