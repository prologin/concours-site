# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('problems', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExplicitSubmissionUnlock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('challenge', models.CharField(max_length=64, db_index=True)),
                ('problem', models.CharField(max_length=64, db_index=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, related_name='explicit_problem_unlocks_created', blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='explicit_problem_unlocks')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='explicitsubmissionunlock',
            unique_together=set([('challenge', 'problem', 'user')]),
        ),
    ]
