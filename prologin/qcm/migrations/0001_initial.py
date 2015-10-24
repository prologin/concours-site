# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contest', '0001_initial'),
        ('sponsor', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('contestant', models.ForeignKey(related_name='qcm_answers', to='contest.Contestant')),
                ('textual_answer', models.TextField(blank=True, null=True, verbose_name=_("Textual answer"))),
            ],
        ),
        migrations.CreateModel(
            name='Proposition',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('text', models.CharField(max_length=255)),
                ('is_correct', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Qcm',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('event', models.ForeignKey(related_name='qcms', to='contest.Event')),
            ],
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('order', models.IntegerField(editable=False, db_index=True)),
                ('body', models.TextField(verbose_name='Question body')),
                ('verbose', models.TextField(blank=True, verbose_name='Verbose description')),
                ('for_sponsor', models.ForeignKey(related_name='qcm_questions', null=True, to='sponsor.Sponsor', blank=True)),
                ('qcm', models.ForeignKey(related_name='questions', to='qcm.Qcm')),
                ('is_open_ended', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('order',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='proposition',
            name='question',
            field=models.ForeignKey(related_name='propositions', to='qcm.Question', verbose_name='Question'),
        ),
        migrations.AddField(
            model_name='answer',
            name='proposition',
            field=models.ForeignKey(related_name='answers', to='qcm.Proposition', verbose_name='Answer'),
        ),
        migrations.AlterUniqueTogether(
            name='answer',
            unique_together={('contestant', 'proposition')},
        ),
    ]
