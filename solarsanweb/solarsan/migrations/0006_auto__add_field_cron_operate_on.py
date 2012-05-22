# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Cron.operate_on'
        db.add_column('solarsan_cron', 'operate_on',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Cron.operate_on'
        db.delete_column('solarsan_cron', 'operate_on')


    models = {
        'solarsan.config': {
            'Meta': {'object_name': 'Config'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'solarsan.cron': {
            'Meta': {'object_name': 'Cron'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'json': ('jsonfield.fields.JSONField', [], {}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128'}),
            'operate_on': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '128'}),
            'run_every': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'task': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'solarsan.dataset': {
            'Exec': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'Meta': {'ordering': "['name', 'creation']", 'object_name': 'Dataset'},
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
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
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
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'failmode': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'free': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'guid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32'}),
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