# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('significance', models.SmallIntegerField(verbose_name='Significance')),
                ('name', models.CharField(max_length=32)),
            ],
            options={
                'verbose_name_plural': 'Rôles',
                'verbose_name': 'Rôle',
                'ordering': ('-significance',),
            },
        ),
        migrations.CreateModel(
            name='TeamMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('year', models.PositiveIntegerField(db_index=True)),
                ('role', models.ForeignKey(related_name='members', to='team.Role', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name='team_memberships', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': "Membres de l'équipe",
                'verbose_name': "Membre de l'équipe",
                'ordering': ['-role__significance', 'user__username'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='teammember',
            unique_together={('user', 'year')},
        ),
    ]
