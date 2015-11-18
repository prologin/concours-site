# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sponsor', '0002_add_order_field'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='sponsor',
            options={},
        ),
        migrations.RemoveField(
            model_name='sponsor',
            name='editions',
        ),
        migrations.RemoveField(
            model_name='sponsor',
            name='order',
        ),
    ]
