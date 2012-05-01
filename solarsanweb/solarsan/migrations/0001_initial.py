# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Config'
        db.create_table('solarsan_config', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('solarsan', ['Config'])

        # Adding model 'Pool'
        db.create_table('solarsan_pool', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('delegation', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('listsnapshots', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('capacity', self.gf('django.db.models.fields.CharField')(max_length=8)),
            ('cachefile', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('free', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('ashift', self.gf('django.db.models.fields.IntegerField')()),
            ('autoreplace', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('bootfs', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('dedupditto', self.gf('django.db.models.fields.IntegerField')()),
            ('dedupratio', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('health', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('failmode', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('version', self.gf('django.db.models.fields.IntegerField')()),
            ('autoexpand', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('allocated', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('altroot', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('size', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('solarsan', ['Pool'])

        # Adding model 'Pool_IOStat'
        db.create_table('solarsan_pool_iostat', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solarsan.Pool'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('timestamp_end', self.gf('django.db.models.fields.DateTimeField')()),
            ('alloc', self.gf('django.db.models.fields.FloatField')()),
            ('free', self.gf('django.db.models.fields.FloatField')()),
            ('bandwidth_read', self.gf('django.db.models.fields.IntegerField')()),
            ('bandwidth_write', self.gf('django.db.models.fields.IntegerField')()),
            ('iops_read', self.gf('django.db.models.fields.IntegerField')()),
            ('iops_write', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('solarsan', ['Pool_IOStat'])

        # Adding model 'Dataset'
        db.create_table('solarsan_dataset', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('basename', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('pool', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solarsan.Pool'])),
            ('setuid', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('referenced', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('zoned', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('primarycache', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('logbias', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('creation', self.gf('django.db.models.fields.DateTimeField')()),
            ('sync', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('dedup', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('sharenfs', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('usedbyrefreservation', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('sharesmb', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('canmount', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('mountpoint', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('casesensitivity', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('utf8only', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('xattr', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mounted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('compression', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('usedbysnapshots', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('copies', self.gf('django.db.models.fields.IntegerField')()),
            ('aclinherit', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('compressratio', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('readonly', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('version', self.gf('django.db.models.fields.IntegerField')()),
            ('normalization', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('secondarycache', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('refreservation', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('available', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('used', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('Exec', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('refquota', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('refcompressratio', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('quota', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('vscan', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('reservation', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('atime', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('recordsize', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('usedbychildren', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('usedbydataset', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('mlslabel', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('checksum', self.gf('django.db.models.fields.CharField')(max_length=32)),
            ('devices', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('nbmand', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('snapdir', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('solarsan', ['Dataset'])

        # Adding model 'Dataset_Cron'
        db.create_table('solarsan_dataset_cron', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=128)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['solarsan.Dataset'])),
            ('recursive', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('task', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('schedule', self.gf('django.db.models.fields.CharField')(max_length=128)),
        ))
        db.send_create_signal('solarsan', ['Dataset_Cron'])


    def backwards(self, orm):
        # Deleting model 'Config'
        db.delete_table('solarsan_config')

        # Deleting model 'Pool'
        db.delete_table('solarsan_pool')

        # Deleting model 'Pool_IOStat'
        db.delete_table('solarsan_pool_iostat')

        # Deleting model 'Dataset'
        db.delete_table('solarsan_dataset')

        # Deleting model 'Dataset_Cron'
        db.delete_table('solarsan_dataset_cron')


    models = {
        'solarsan.config': {
            'Meta': {'object_name': 'Config'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'solarsan.dataset': {
            'Exec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'object_name': 'Dataset'},
            'aclinherit': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'atime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'available': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'basename': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'canmount': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'casesensitivity': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'checksum': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'compression': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'compressratio': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'copies': ('django.db.models.fields.IntegerField', [], {}),
            'creation': ('django.db.models.fields.DateTimeField', [], {}),
            'dedup': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'devices': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'logbias': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'mlslabel': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'mounted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mountpoint': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'nbmand': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'normalization': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['solarsan.Pool']"}),
            'primarycache': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'quota': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'recordsize': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'refcompressratio': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'referenced': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'refquota': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'refreservation': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'reservation': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'secondarycache': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'setuid': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sharenfs': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sharesmb': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'snapdir': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'sync': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'used': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'usedbychildren': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'usedbydataset': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'usedbyrefreservation': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'usedbysnapshots': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'utf8only': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'version': ('django.db.models.fields.IntegerField', [], {}),
            'vscan': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'xattr': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'zoned': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'solarsan.dataset_cron': {
            'Meta': {'object_name': 'Dataset_Cron'},
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['solarsan.Dataset']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'recursive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schedule': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'solarsan.pool': {
            'Meta': {'object_name': 'Pool'},
            'allocated': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'altroot': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'ashift': ('django.db.models.fields.IntegerField', [], {}),
            'autoexpand': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'autoreplace': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bootfs': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'cachefile': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'capacity': ('django.db.models.fields.CharField', [], {'max_length': '8'}),
            'dedupditto': ('django.db.models.fields.IntegerField', [], {}),
            'dedupratio': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'delegation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'failmode': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'free': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'health': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'listsnapshots': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'readonly': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'size': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'version': ('django.db.models.fields.IntegerField', [], {})
        },
        'solarsan.pool_iostat': {
            'Meta': {'object_name': 'Pool_IOStat'},
            'alloc': ('django.db.models.fields.FloatField', [], {}),
            'bandwidth_read': ('django.db.models.fields.IntegerField', [], {}),
            'bandwidth_write': ('django.db.models.fields.IntegerField', [], {}),
            'free': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'iops_read': ('django.db.models.fields.IntegerField', [], {}),
            'iops_write': ('django.db.models.fields.IntegerField', [], {}),
            'pool': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['solarsan.Pool']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'timestamp_end': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['solarsan']