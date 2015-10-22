# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import forum.models
import prologin.models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(verbose_name='Name', max_length=255)),
                ('slug', models.SlugField(max_length=300)),
                ('description', models.TextField(verbose_name='Description')),
                ('order', models.IntegerField(db_index=True, editable=False)),
                ('thread_count', models.PositiveIntegerField(blank=True, verbose_name='Number of threads', editable=False, default=0)),
                ('post_count', models.PositiveIntegerField(blank=True, verbose_name='Number of posts', editable=False, default=0)),
            ],
            options={
                'ordering': ('order',),
                'verbose_name_plural': 'Forums',
                'permissions': (('view_forum', 'View forum'),),
                'verbose_name': 'Forum',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('content', models.TextField(verbose_name='Content')),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_last_edited', models.DateTimeField(auto_now=True)),
                ('last_edited_reason', models.TextField(blank=True, verbose_name='Edit reason')),
                ('is_visible', models.BooleanField(db_index=True, default=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='forum_posts')),
                ('last_edited_author', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, related_name='forum_last_edited_posts', null=True)),
            ],
            options={
                'ordering': ('date_created',),
                'verbose_name_plural': 'Posts',
                'verbose_name': 'Post',
                'get_latest_by': 'date_created',
            },
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(verbose_name='Title', max_length=255)),
                ('slug', models.SlugField(max_length=300)),
                ('type', prologin.models.EnumField(forum.models.Thread.Type, db_index=True, choices=[(0, 'Normal'), (1, 'Sticky'), (2, 'Announce')], verbose_name='Thread type', default=0)),
                ('status', prologin.models.EnumField(forum.models.Thread.Status, db_index=True, choices=[(0, 'Normal'), (1, 'Closed'), (2, 'Moved')], verbose_name='Thread status', default=0)),
                ('is_visible', models.BooleanField(db_index=True, verbose_name='Visible', default=True)),
                ('date_last_edited', models.DateTimeField(auto_now=True)),
                ('post_count', models.PositiveIntegerField(blank=True, verbose_name='Number of posts', editable=False, default=0)),
                ('date_last_post', models.DateTimeField(blank=True, null=True, verbose_name='Last post added on')),
                ('forum', models.ForeignKey(to='forum.Forum', related_name='threads')),
                ('last_edited_author', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True, related_name='forum_last_edited_threads', null=True)),
            ],
            options={
                'ordering': ('-type', '-date_last_post'),
                'verbose_name_plural': 'Threads',
                'verbose_name': 'Thread',
                'get_latest_by': 'date_last_post',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(to='forum.Thread', related_name='posts'),
        ),
    ]
