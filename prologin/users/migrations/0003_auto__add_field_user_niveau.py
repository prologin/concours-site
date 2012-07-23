# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.niveau'
        db.add_column('users_user', 'niveau',
                      self.gf('django.db.models.fields.CharField')(default=u'Th\xc3\xa8se', max_length=32),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.niveau'
        db.delete_column('users_user', 'niveau')


    models = {
        'users.user': {
            'Meta': {'object_name': 'User'},
            'adresse': ('django.db.models.fields.TextField', [], {}),
            'code_postal': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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