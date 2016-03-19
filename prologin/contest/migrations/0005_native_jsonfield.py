# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations


def noop(*args):
    pass


def contrib_jsonfield_to_native(apps, schema_editor):
    model = apps.get_model('contest', 'ContestantCorrection')._meta
    schema_editor.execute("ALTER TABLE {tbl} ALTER COLUMN {col} TYPE jsonb USING {col}::jsonb;".format(
        tbl=model.db_table,
        col=model.get_field('changes').column,
    ))


def native_jsonfield_to_contrib(apps, schema_editor):
    model = apps.get_model('contest', 'ContestantCorrection')._meta
    schema_editor.execute("ALTER TABLE {tbl} ALTER COLUMN {col} TYPE text USING {col}::text;".format(
        tbl=model.db_table,
        col=model.get_field('changes').column,
    ))


class Migration(migrations.Migration):
    dependencies = [
        ('contest', '0004_edition_correction_flags'),
    ]

    operations = [
        migrations.RunPython(contrib_jsonfield_to_native, noop),
        migrations.AlterField(
            model_name='contestantcorrection',
            name='changes',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True),
        ),
        migrations.RunPython(noop, native_jsonfield_to_contrib),
    ]
