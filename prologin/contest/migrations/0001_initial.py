# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Contest'
        db.create_table('contest_contest', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('contest', ['Contest'])

        # Adding model 'Event'
        db.create_table('contest_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contest.Contest'])),
            ('center', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['centers.Center'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=17)),
            ('begin', self.gf('django.db.models.fields.DateTimeField')()),
            ('end', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('contest', ['Event'])

        # Adding model 'Contestant'
        db.create_table('contest_contestant', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('contest', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contest.Contest'])),
        ))
        db.send_create_signal('contest', ['Contestant'])

        # Adding M2M table for field event_choices on 'Contestant'
        db.create_table('contest_contestant_event_choices', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('contestant', models.ForeignKey(orm['contest.contestant'], null=False)),
            ('event', models.ForeignKey(orm['contest.event'], null=False))
        ))
        db.create_unique('contest_contestant_event_choices', ['contestant_id', 'event_id'])

        # Adding M2M table for field events on 'Contestant'
        db.create_table('contest_contestant_events', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('contestant', models.ForeignKey(orm['contest.contestant'], null=False)),
            ('event', models.ForeignKey(orm['contest.event'], null=False))
        ))
        db.create_unique('contest_contestant_events', ['contestant_id', 'event_id'])

        # Adding model 'Score'
        db.create_table('contest_score', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('contestant', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contest.Contestant'])),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=42)),
            ('score', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('contest', ['Score'])


    def backwards(self, orm):
        # Deleting model 'Contest'
        db.delete_table('contest_contest')

        # Deleting model 'Event'
        db.delete_table('contest_event')

        # Deleting model 'Contestant'
        db.delete_table('contest_contestant')

        # Removing M2M table for field event_choices on 'Contestant'
        db.delete_table('contest_contestant_event_choices')

        # Removing M2M table for field events on 'Contestant'
        db.delete_table('contest_contestant_events')

        # Deleting model 'Score'
        db.delete_table('contest_score')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
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
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'contest.contest': {
            'Meta': {'object_name': 'Contest'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {})
        },
        'contest.contestant': {
            'Meta': {'object_name': 'Contestant'},
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contest.Contest']"}),
            'event_choices': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'choices'", 'symmetrical': 'False', 'to': "orm['contest.Event']"}),
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['contest.Event']", 'symmetrical': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'contest.event': {
            'Meta': {'object_name': 'Event'},
            'begin': ('django.db.models.fields.DateTimeField', [], {}),
            'center': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['centers.Center']"}),
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contest.Contest']"}),
            'end': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '17'})
        },
        'contest.score': {
            'Meta': {'object_name': 'Score'},
            'contestant': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contest.Contestant']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('django.db.models.fields.IntegerField', [], {}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '42'})
        }
    }

    complete_apps = ['contest']