# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.birthday'
        db.add_column('users_user', 'birthday',
                      self.gf('django.db.models.fields.CharField')(default='27/02/1990', max_length=64),
                      keep_default=False)

        # Adding field 'User.newsletter'
        db.add_column('users_user', 'newsletter',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.birthday'
        db.delete_column('users_user', 'birthday')

        # Deleting field 'User.newsletter'
        db.delete_column('users_user', 'newsletter')


    models = {
        'users.user': {
            'Meta': {'object_name': 'User'},
            'adresse': ('django.db.models.fields.TextField', [], {}),
            'birthday': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'code_postal': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'niveau': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'nom': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'prenom': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'titre': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'ville': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['users']