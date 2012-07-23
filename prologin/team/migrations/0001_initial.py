# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Role'
        db.create_table('team_role', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rank', self.gf('django.db.models.fields.IntegerField')()),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('team', ['Role'])

        # Adding model 'Team'
        db.create_table('team_team', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
            ('nick', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['team.Role'])),
        ))
        db.send_create_signal('team', ['Team'])


    def backwards(self, orm):
        # Deleting model 'Role'
        db.delete_table('team_role')

        # Deleting model 'Team'
        db.delete_table('team_team')


    models = {
        'team.role': {
            'Meta': {'object_name': 'Role'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rank': ('django.db.models.fields.IntegerField', [], {}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '32'})
        },
        'team.team': {
            'Meta': {'object_name': 'Team'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['team.Role']"}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        }
    }

    complete_apps = ['team']