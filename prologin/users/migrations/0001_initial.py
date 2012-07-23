# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'User'
        db.create_table('users_user', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('nick', self.gf('django.db.models.fields.CharField')(max_length=64)),
        ))
        db.send_create_signal('users', ['User'])


    def backwards(self, orm):
        # Deleting model 'User'
        db.delete_table('users_user')


    models = {
        'users.user': {
            'Meta': {'object_name': 'User'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['users']