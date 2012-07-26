# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Center.nom'
        db.delete_column('centers_center', 'nom')

        # Deleting field 'Center.tel'
        db.delete_column('centers_center', 'tel')

        # Deleting field 'Center.ville'
        db.delete_column('centers_center', 'ville')

        # Deleting field 'Center.adresse'
        db.delete_column('centers_center', 'adresse')

        # Deleting field 'Center.commentaires'
        db.delete_column('centers_center', 'commentaires')

        # Adding field 'Center.city'
        db.add_column('centers_center', 'city',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=64),
                      keep_default=False)

        # Adding field 'Center.name'
        db.add_column('centers_center', 'name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=64),
                      keep_default=False)

        # Adding field 'Center.address'
        db.add_column('centers_center', 'address',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128),
                      keep_default=False)

        # Adding field 'Center.phone_number'
        db.add_column('centers_center', 'phone_number',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=10, blank=True),
                      keep_default=False)

        # Adding field 'Center.comments'
        db.add_column('centers_center', 'comments',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'Center.nom'
        raise RuntimeError("Cannot reverse this migration. 'Center.nom' and its values cannot be restored.")
        # Adding field 'Center.tel'
        db.add_column('centers_center', 'tel',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=10, blank=True),
                      keep_default=False)


        # User chose to not deal with backwards NULL issues for 'Center.ville'
        raise RuntimeError("Cannot reverse this migration. 'Center.ville' and its values cannot be restored.")

        # User chose to not deal with backwards NULL issues for 'Center.adresse'
        raise RuntimeError("Cannot reverse this migration. 'Center.adresse' and its values cannot be restored.")
        # Adding field 'Center.commentaires'
        db.add_column('centers_center', 'commentaires',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Deleting field 'Center.city'
        db.delete_column('centers_center', 'city')

        # Deleting field 'Center.name'
        db.delete_column('centers_center', 'name')

        # Deleting field 'Center.address'
        db.delete_column('centers_center', 'address')

        # Deleting field 'Center.phone_number'
        db.delete_column('centers_center', 'phone_number')

        # Deleting field 'Center.comments'
        db.delete_column('centers_center', 'comments')


    models = {
        'centers.center': {
            'Meta': {'object_name': 'Center'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'comments': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'lat': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '16', 'decimal_places': '6'}),
            'lng': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '16', 'decimal_places': '6'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'phone_number': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'})
        }
    }

    complete_apps = ['centers']