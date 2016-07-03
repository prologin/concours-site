# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
import django.db.models.deletion
from django.db import migrations, connection


def thirdparty_jsonfield_to_native(apps, schema_editor):
    if connection.vendor != 'postgresql':
        return
    model = apps.get_model('contest', 'ContestantCorrection')._meta
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT pg_typeof({col}) from {tbl} LIMIT 1".format(
            tbl=model.db_table,
            col=model.get_field('changes').column,
        ))
        b_typeof = cursor.fetchone()
    try:
        typeof = b_typeof[0]
    except:
        return
    if typeof == "jsonb":
        # already native
        print("\n    Not converting raw text JSON to Postgres jsonb (already jsonb)", end="\n   ")
        return
    schema_editor.execute("ALTER TABLE {tbl} ALTER COLUMN {col} TYPE jsonb USING {col}::jsonb;".format(
        tbl=model.db_table,
        col=model.get_field('changes').column,
    ))


def native_jsonfield_to_thirdparty(apps, schema_editor):
    if connection.vendor != 'postgresql':
        return
    try:
        from jsonfield import JSONField
    except ImportError:
        raise ValueError("django_jsonfield module is not installed; cannot migrate backwards")
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
        migrations.RunPython(thirdparty_jsonfield_to_native, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='contestantcorrection',
            name='changes',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True),
        ),
        migrations.RunPython(migrations.RunPython.noop, native_jsonfield_to_thirdparty),
    ]
