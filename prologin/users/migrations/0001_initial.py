# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.auth.models
from django.conf import settings
from prologin.utils import upload_path
import timezone_field.fields
import django.utils.timezone
import django.core.validators

import prologin.models
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProloginUser',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, blank=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', default=False, help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=30, unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='last name')),
                ('email', models.EmailField(db_index=True, max_length=254, unique=True, verbose_name='email address')),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('address', models.TextField(blank=True, verbose_name='Address')),
                ('postal_code', models.CharField(blank=True, max_length=32, verbose_name='Postal code')),
                ('city', models.CharField(blank=True, max_length=64, verbose_name='City')),
                ('country', models.CharField(blank=True, max_length=64, verbose_name='Country')),
                ('gender', prologin.models.GenderField(choices=[(None, 'Prefer not to tell'), (0, 'Male'), (1, 'Female')], null=True, blank=True, verbose_name='Gender', db_index=True)),
                ('school_stage', prologin.models.EnumField(users.models.EducationStage, null=True, db_index=True, verbose_name='Educational stage', choices=[(0, 'Middle school'), (1, 'High school'), (2, 'Bac'), (3, 'Bac+1'), (4, 'Bac+2'), (5, 'Bac+3'), (6, 'Bac+4'), (7, 'Bac+5'), (8, 'Bac+6 and after'), (9, 'Other'), (10, 'Former student')], blank=True)),
                ('phone', models.CharField(blank=True, max_length=16, verbose_name='Phone')),
                ('birthday', models.DateField(null=True, blank=True, verbose_name='Birth day')),
                ('allow_mailing', models.BooleanField(db_index=True, verbose_name='Allow Prologin to send me emails', default=True, help_text='We only mail you to provide useful information during the various stages of the contest. We hate spam as much as you do!')),
                ('signature', models.TextField(blank=True, verbose_name='Signature')),
                ('preferred_language', prologin.models.CodingLanguageField(blank=True, choices=[('ada', 'Ada'), ('brainfuck', 'Brainfuck'), ('c', 'C'), ('csharp', 'C#'), ('cpp', 'C++'), ('fsharp', 'F#'), ('haskell', 'Haskell'), ('java', 'Java'), ('js', 'Javascript'), ('lua', 'Lua'), ('ocaml', 'OCaml'), ('pascal', 'Pascal'), ('perl', 'Perl'), ('php', 'PHP'), ('pseudocode', 'Pseudocode'), ('python2', 'Python 2'), ('python3', 'Python 3'), ('scheme', 'Scheme'), ('vb', 'Visual Basic')], db_index=True, max_length=64, verbose_name='Preferred coding language')),
                ('timezone', timezone_field.fields.TimeZoneField(verbose_name='Time zone', default='Europe/Paris')),
                ('preferred_locale', models.CharField(blank=True, choices=[('en', 'English'), ('fr', 'French')], max_length=8, verbose_name='Locale')),
                ('avatar', models.ImageField(blank=True, verbose_name='Profile picture', upload_to=users.models.ProloginUser.upload_avatar_to)),
                ('picture', models.ImageField(blank=True, verbose_name='Official member picture', upload_to=users.models.ProloginUser.upload_picture_to)),
                ('legacy_md5_password', models.CharField(blank=True, max_length=32)),
                ('groups', models.ManyToManyField(blank=True, related_query_name='user', to='auth.Group', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, related_query_name='user', to='auth.Permission', help_text='Specific permissions for this user.', related_name='user_set', verbose_name='user permissions')),
            ],
            options={
                'verbose_name_plural': 'users',
                'abstract': False,
                'verbose_name': 'user',
            },
            managers=[
                ('objects', users.models.ProloginUserManager()),
            ],
        ),
        migrations.CreateModel(
            name='UserActivation',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('slug', models.SlugField(max_length=32)),
                ('expiration_date', models.DateTimeField()),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='activation')),
            ],
        ),

    ]
