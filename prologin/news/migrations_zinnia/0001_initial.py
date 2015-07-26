# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import tagging.fields
import django.utils.timezone
import zinnia.models_bases.entry
import django.contrib.auth.models
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('sites', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('slug', models.SlugField(help_text="Used to build the category's URL.", unique=True, verbose_name='slug', max_length=255)),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(verbose_name='parent category', to='zinnia.Category', null=True, related_name='children', blank=True)),
            ],
            options={
                'ordering': ['title'],
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
        ),
        migrations.CreateModel(
            name='Entry',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('slug', models.SlugField(help_text="Used to build the entry's URL.", unique_for_date='creation_date', verbose_name='slug', max_length=255)),
                ('status', models.IntegerField(choices=[(0, 'draft'), (1, 'hidden'), (2, 'published')], verbose_name='status', default=0, db_index=True)),
                ('start_publication', models.DateTimeField(help_text='Start date of publication.', null=True, blank=True, verbose_name='start publication', db_index=True)),
                ('end_publication', models.DateTimeField(help_text='End date of publication.', null=True, blank=True, verbose_name='end publication', db_index=True)),
                ('creation_date', models.DateTimeField(help_text="Used to build the entry's URL.", verbose_name='creation date', default=django.utils.timezone.now, db_index=True)),
                ('last_update', models.DateTimeField(verbose_name='last update', default=django.utils.timezone.now)),
                ('content', models.TextField(blank=True, verbose_name='content')),
                ('comment_enabled', models.BooleanField(help_text='Allows comments if checked.', verbose_name='comments enabled', default=True)),
                ('pingback_enabled', models.BooleanField(help_text='Allows pingbacks if checked.', verbose_name='pingbacks enabled', default=True)),
                ('trackback_enabled', models.BooleanField(help_text='Allows trackbacks if checked.', verbose_name='trackbacks enabled', default=True)),
                ('comment_count', models.IntegerField(verbose_name='comment count', default=0)),
                ('pingback_count', models.IntegerField(verbose_name='pingback count', default=0)),
                ('trackback_count', models.IntegerField(verbose_name='trackback count', default=0)),
                ('lead', models.TextField(help_text='Lead paragraph', blank=True, verbose_name='lead')),
                ('excerpt', models.TextField(help_text='Used for SEO purposes.', blank=True, verbose_name='excerpt')),
                ('image', models.ImageField(help_text='Used for illustration.', upload_to=zinnia.models_bases.entry.image_upload_to_dispatcher, verbose_name='image', blank=True)),
                ('image_caption', models.TextField(help_text="Image's caption.", blank=True, verbose_name='caption')),
                ('featured', models.BooleanField(verbose_name='featured', default=False)),
                ('tags', tagging.fields.TagField(verbose_name='tags', max_length=255, blank=True)),
                ('login_required', models.BooleanField(help_text='Only authenticated users can view the entry.', verbose_name='login required', default=False)),
                ('password', models.CharField(help_text='Protects the entry with a password.', verbose_name='password', max_length=50, blank=True)),
                ('content_template', models.CharField(verbose_name='content template', help_text="Template used to display the entry's content.", choices=[('zinnia/_entry_detail.html', 'Default template')], max_length=250, default='zinnia/_entry_detail.html')),
                ('detail_template', models.CharField(verbose_name='detail template', help_text="Template used to display the entry's detail page.", choices=[('entry_detail.html', 'Default template')], max_length=250, default='entry_detail.html')),
            ],
            options={
                'verbose_name_plural': 'entries',
                'ordering': ['-creation_date'],
                'get_latest_by': 'creation_date',
                'abstract': False,
                'permissions': (('can_view_all', 'Can view all entries'), ('can_change_status', 'Can change status'), ('can_change_author', 'Can change author(s)')),
                'verbose_name': 'entry',
            },
        ),
        migrations.CreateModel(
            name='Author',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('users.prologinuser', models.Model),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='entry',
            name='authors',
            field=models.ManyToManyField(to='zinnia.Author', related_name='entries', blank=True, verbose_name='authors'),
        ),
        migrations.AddField(
            model_name='entry',
            name='categories',
            field=models.ManyToManyField(to='zinnia.Category', related_name='entries', blank=True, verbose_name='categories'),
        ),
        migrations.AddField(
            model_name='entry',
            name='related',
            field=models.ManyToManyField(to='zinnia.Entry', related_name='related_rel_+', blank=True, verbose_name='related entries'),
        ),
        migrations.AddField(
            model_name='entry',
            name='sites',
            field=models.ManyToManyField(to='sites.Site', related_name='entries', help_text='Sites where the entry will be published.', verbose_name='sites'),
        ),
        migrations.AlterIndexTogether(
            name='entry',
            index_together=set([('slug', 'creation_date'), ('status', 'creation_date', 'start_publication', 'end_publication')]),
        ),
    ]
