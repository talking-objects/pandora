# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'Stream'
        db.delete_table('archive_stream')

        # Deleting model 'FileContents'
        db.delete_table('archive_filecontents')

        # Adding field 'File.video_available'
        db.add_column('archive_file', 'video_available', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True), keep_default=False)

        # Adding field 'File.video'
        db.add_column('archive_file', 'video', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'File.data'
        db.add_column('archive_file', 'data', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'Stream'
        db.create_table('archive_stream', (
            ('available', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('profile', self.gf('django.db.models.fields.CharField')(default='96p.webm', max_length=255)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(default=None, related_name='derivatives', null=True, to=orm['archive.Stream'])),
            ('video', self.gf('django.db.models.fields.files.FileField')(default=None, max_length=100, blank=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(related_name='streams', to=orm['archive.File'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('archive', ['Stream'])

        # Adding model 'FileContents'
        db.create_table('archive_filecontents', (
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(related_name='contents', to=orm['archive.File'])),
            ('data', self.gf('django.db.models.fields.TextField')(default=u'')),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('archive', ['FileContents'])

        # Deleting field 'File.video_available'
        db.delete_column('archive_file', 'video_available')

        # Deleting field 'File.video'
        db.delete_column('archive_file', 'video')

        # Deleting field 'File.data'
        db.delete_column('archive_file', 'data')


    models = {
        'archive.file': {
            'Meta': {'object_name': 'File'},
            'audio_codec': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'bits_per_pixel': ('django.db.models.fields.FloatField', [], {'default': '-1'}),
            'channels': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'data': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'display_aspect_ratio': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'episode': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'framerate': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'height': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('oxdjango.fields.DictField', [], {'default': '{}'}),
            'is_audio': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_extra': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_main': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_subtitle': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_version': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_video': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '8'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'movie': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['backend.Movie']"}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2048'}),
            'oshash': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '16'}),
            'part': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'pixel_format': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'pixels': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'samplerate': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'season': ('django.db.models.fields.IntegerField', [], {'default': '-1'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '2048'}),
            'verified': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'version': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'video': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'video_available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'video_codec': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'width': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'archive.fileinstance': {
            'Meta': {'unique_together': "(('name', 'folder', 'volume'),)", 'object_name': 'Instance'},
            'atime': ('django.db.models.fields.IntegerField', [], {'default': '1282732467'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'ctime': ('django.db.models.fields.IntegerField', [], {'default': '1282732467'}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'instances'", 'to': "orm['archive.File']"}),
            'folder': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'mtime': ('django.db.models.fields.IntegerField', [], {'default': '1282732467'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2048'}),
            'volume': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'files'", 'to': "orm['archive.Volume']"})
        },
        'archive.frame': {
            'Meta': {'unique_together': "(('file', 'position'),)", 'object_name': 'Frame'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'frames'", 'to': "orm['archive.File']"}),
            'frame': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.FloatField', [], {})
        },
        'archive.volume': {
            'Meta': {'unique_together': "(('user', 'name'),)", 'object_name': 'Volume'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'volumes'", 'to': "orm['auth.User']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'backend.movie': {
            'Meta': {'object_name': 'Movie'},
            'available': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'imdb': ('oxdjango.fields.DictField', [], {'default': '{}'}),
            'json': ('oxdjango.fields.DictField', [], {'default': '{}'}),
            'metadata': ('oxdjango.fields.DictField', [], {'default': '{}'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'movieId': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '128', 'blank': 'True'}),
            'oxdbId': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '42', 'blank': 'True'}),
            'poster': ('django.db.models.fields.files.ImageField', [], {'default': 'None', 'max_length': '100', 'blank': 'True'}),
            'poster_frame': ('django.db.models.fields.FloatField', [], {'default': '-1'}),
            'poster_height': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'poster_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'poster_width': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'stream_aspect': ('django.db.models.fields.FloatField', [], {'default': '1.3333333333333333'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['archive']
