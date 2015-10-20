# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import forum.models
from django.conf import settings
import django.utils.timezone
import prologin.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Forum',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=255, verbose_name='Name')),
                ('slug', models.SlugField(max_length=300)),
                ('description', models.TextField(verbose_name='Description')),
                ('order', models.IntegerField(editable=False, db_index=True)),
                ('post_count', models.PositiveIntegerField(default=0, verbose_name='Number of posts', editable=False, blank=True)),
                ('thread_count', models.PositiveIntegerField(default=0, verbose_name='Number of threads', editable=False, blank=True)),
                ('date_last_post', models.DateTimeField(verbose_name='Last post added on', null=True, blank=True)),
            ],
            options={
                'verbose_name_plural': 'Forums',
                'verbose_name': 'Forum',
                'permissions': (('view_forum', 'View forum'),),
                'ordering': ('order',),
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('content', models.TextField(verbose_name='Content')),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_last_edited', models.DateTimeField(auto_now=True)),
                ('last_edited_reason', models.TextField(verbose_name='Edit reason', blank=True)),
                ('is_visible', models.BooleanField(default=True, db_index=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='forum_posts')),
                ('last_edited_author', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='forum_last_edited_posts')),
            ],
            options={
                'verbose_name_plural': 'Posts',
                'verbose_name': 'Post',
                'ordering': ('date_created',),
                'get_latest_by': 'date_created',
            },
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('title', models.CharField(max_length=255, verbose_name='Title')),
                ('slug', models.SlugField(max_length=300)),
                ('type', prologin.models.EnumField(forum.models.Thread.Type, default=0, verbose_name='Thread type', db_index=True, choices=[(0, 'Normal'), (1, 'Sticky'), (2, 'Announce')])),
                ('status', prologin.models.EnumField(forum.models.Thread.Status, default=0, verbose_name='Thread status', db_index=True, choices=[(0, 'Normal'), (1, 'Closed'), (2, 'Moved')])),
                ('is_visible', models.BooleanField(default=True, verbose_name='Visible', db_index=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_last_edited', models.DateTimeField(auto_now=True)),
                ('post_count', models.PositiveIntegerField(default=0, verbose_name='Posts count', editable=False, blank=True)),
                ('view_count', models.PositiveIntegerField(default=0, verbose_name='Views count', editable=False, blank=True)),
                ('date_last_post', models.DateTimeField(verbose_name='Last post added on', null=True, blank=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='forum_threads')),
                ('forum', models.ForeignKey(to='forum.Forum', related_name='threads')),
                ('last_edited_author', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True, related_name='forum_last_edited_threads')),
            ],
            options={
                'verbose_name_plural': 'Threads',
                'verbose_name': 'Thread',
                'ordering': ('-type', '-date_last_post'),
                'get_latest_by': 'date_last_post',
            },
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(to='forum.Thread', related_name='posts'),
        ),
    ]
