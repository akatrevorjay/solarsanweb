from django.db import models
#from jsonfield import JSONField
import logging
#from django.utils import timezone
#from solarsan.utils import FilterableDict, convert_bytes_to_human, convert_human_to_bytes
import zfs
import mongoengine as m


"""
Config
"""

class Config(m.Document):
    meta = {'collection': 'config',}
    name = m.StringField(unique=True)
    config = m.DictField()
    created = m.DateTimeField()
    modified = m.DateTimeField()




class EnabledModelManager(models.Manager):
    """ Returns objects that have enabled=True """
    def get_query_set(self):
        return super(EnabledModelManager, self).get_query_set().filter(enabled=True)

#class Snapshot_Backup_Log(models.Model):
#    dataset = models.ForeignKey(Dataset)
#    date = models.DateTimeField('log timestamp')
#    success = models.BooleanField()
#    description = models.CharField(max_length=255)


## Schedule backups, snapshots, health status checks, etc
#class Cron(models.Model):
#    name = models.CharField(max_length=128, unique=True)
#    last_modified = models.DateTimeField(auto_now=True)
#    last_ret = models.IntegerField(default=0)
#    enabled = models.BooleanField(default=True)
#    run_every = models.IntegerField(default=0)
#    operate_on = models.CharField(max_length=128, default='')
#
#    task = models.CharField(max_length=128)
#    json = JSONField()
#
#    def __unicode__(self):
#        suffix = []
#        if not self.enabled: suffix.append("disabled")
#
#        if suffix: suffix = ' (' + ','.join(suffix) + ')'
#        else: suffix = ''
#        return '%s:%s%s' % (self.task, self.name, suffix)

##
## Auth/User
##

from django.contrib.auth.models import User
from django.db.models.signals import post_save

#class UserProfile(models.Model):
#    # This field is required.
#    user = models.OneToOneField(User)
#
#    # Other fields here
#    #accepted_eula = models.BooleanField()
#    #favorite_animal = models.CharField(max_length=20, default="Dragons.")

### Upon User object creation, create a UserProfile for him/her
#def create_user_profile(sender, instance, created, **kwargs):
#    if created:
#        UserProfile.objects.create(user=instance)
#
#post_save.connect(create_user_profile, sender=User)


