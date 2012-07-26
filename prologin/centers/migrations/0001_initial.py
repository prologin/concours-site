# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Center'
        db.create_table('centers_center', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ville', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('nom', self.gf('django.db.models.fields.CharField')(max_length=64)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=1)),
            ('adresse', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('tel', self.gf('django.db.models.fields.CharField')(max_length=10, blank=True)),
            ('commentaires', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('lat', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=16, decimal_places=6)),
            ('lng', self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=16, decimal_places=6)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('centers', ['Center'])


    def backwards(self, orm):
        # Deleting model 'Center'
        db.delete_table('centers_center')


    models = {
        'centers.center': {
            'Meta': {'object_name': 'Center'},
            'adresse': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'commentaires': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'lat': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '16', 'decimal_places': '6'}),
            'lng': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '16', 'decimal_places': '6'}),
            'nom': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'tel': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'ville': ('django.db.models.fields.CharField', [], {'max_length': '64'})
        }
    }

    complete_apps = ['centers']