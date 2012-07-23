# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'User.titre'
        db.add_column('users_user', 'titre',
                      self.gf('django.db.models.fields.CharField')(default='Monsieur', max_length=16),
                      keep_default=False)

        # Adding field 'User.prenom'
        db.add_column('users_user', 'prenom',
                      self.gf('django.db.models.fields.CharField')(default=u'Jill-J\xc3\xaann', max_length=64),
                      keep_default=False)

        # Adding field 'User.nom'
        db.add_column('users_user', 'nom',
                      self.gf('django.db.models.fields.CharField')(default='Vie', max_length=64),
                      keep_default=False)

        # Adding field 'User.adresse'
        db.add_column('users_user', 'adresse',
                      self.gf('django.db.models.fields.TextField')(default='12 rue Menpenti'),
                      keep_default=False)

        # Adding field 'User.code_postal'
        db.add_column('users_user', 'code_postal',
                      self.gf('django.db.models.fields.CharField')(default='13006', max_length=5),
                      keep_default=False)

        # Adding field 'User.ville'
        db.add_column('users_user', 'ville',
                      self.gf('django.db.models.fields.CharField')(default='Marseille', max_length=64),
                      keep_default=False)

        # Adding field 'User.number'
        db.add_column('users_user', 'number',
                      self.gf('django.db.models.fields.CharField')(default='0642623974', max_length=16),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'User.titre'
        db.delete_column('users_user', 'titre')

        # Deleting field 'User.prenom'
        db.delete_column('users_user', 'prenom')

        # Deleting field 'User.nom'
        db.delete_column('users_user', 'nom')

        # Deleting field 'User.adresse'
        db.delete_column('users_user', 'adresse')

        # Deleting field 'User.code_postal'
        db.delete_column('users_user', 'code_postal')

        # Deleting field 'User.ville'
        db.delete_column('users_user', 'ville')

        # Deleting field 'User.number'
        db.delete_column('users_user', 'number')


    models = {
        'users.user': {
            'Meta': {'object_name': 'User'},
            'adresse': ('django.db.models.fields.TextField', [], {}),
            'code_postal': ('django.db.models.fields.CharField', [], {'max_length': '5'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'nick': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'nom': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'number': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'prenom': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'titre': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'ville': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['users']