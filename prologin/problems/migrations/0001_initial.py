# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models, migrations

import prologin.models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('challenge', models.CharField(db_index=True, max_length=64)),
                ('problem', models.CharField(db_index=True, max_length=64)),
                ('score_base', models.IntegerField(default=0)),
                ('malus', models.IntegerField(default=0)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='training_submissions')),
            ],
            options={
                'verbose_name_plural': 'Submissions',
                'verbose_name': 'Submission',
            },
        ),
        migrations.CreateModel(
            name='SubmissionCode',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('language', prologin.models.CodingLanguageField(max_length=64, choices=[('ada', 'Ada'), ('brainfuck', 'Brainfuck'), ('c', 'C'), ('csharp', 'C#'), ('cpp', 'C++'), ('fsharp', 'F#'), ('haskell', 'Haskell'), ('java', 'Java'), ('js', 'Javascript'), ('lua', 'Lua'), ('ocaml', 'OCaml'), ('pascal', 'Pascal'), ('perl', 'Perl'), ('php', 'PHP'), ('pseudocode', 'Pseudocode'), ('python2', 'Python 2'), ('python3', 'Python 3'), ('scheme', 'Scheme'), ('vb', 'VB')], verbose_name='Coding language')),
                ('code', models.TextField()),
                ('summary', models.TextField(blank=True)),
                ('score', models.IntegerField(null=True, blank=True)),
                ('exec_time', models.IntegerField(null=True, blank=True)),
                ('exec_memory', models.IntegerField(null=True, blank=True)),
                ('date_submitted', models.DateTimeField(default=django.utils.timezone.now)),
                ('submission', models.ForeignKey(to='problems.Submission', related_name='codes')),
            ],
            options={
                'verbose_name': 'Submission code',
                'ordering': ('-date_submitted', '-pk'),
                'verbose_name_plural': 'Submission codes',
                'get_latest_by': 'date_submitted',
            },
        ),
        migrations.CreateModel(
            name='SubmissionCodeChoice',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('code', models.ForeignKey(related_name='submission_code_choices', to='problems.SubmissionCode')),
                ('submission', models.ForeignKey(related_name='submission_choices', to='problems.Submission')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='submissioncodechoice',
            unique_together=set([('submission', 'code')]),
        ),
        migrations.AlterUniqueTogether(
            name='submission',
            unique_together=set([('challenge', 'problem', 'user')]),
        ),
    ]
