# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Team.nick'
        db.delete_column('team_team', 'nick')

        # Adding field 'Team.uid'
        db.add_column('team_team', 'uid',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['users.User']),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Team.nick'
        db.add_column('team_team', 'nick',
                      self.gf('django.db.models.fields.CharField')(default=1, max_length=64),
                      keep_default=False)

        # Deleting field 'Team.uid'
        db.delete_column('team_team', 'uid_id')


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
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['team.Role']"}),
            'uid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['users.User']"}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        'users.user': {
            'Meta': {'object_name': 'User'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['team']