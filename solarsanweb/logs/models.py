#from django.db import models
import mongoengine


class LogEntry(mongoengine.DynamicDocument):
    meta = {'collection': 'messages',
            'db_alias': 'syslog',
            #'max_size': 1024 * 1024 * 256,
            'allow_inheritance': False,
            }

    def __getattribute__(self, key):
        """THIS IS A HACK"""
        upkey = key.upper()
        if key != '__dict__' and key not in self.__dict__ and key.islower() and upkey in self.__dict__:
            key = upkey
        return super(LogEntry, self).__getattribute__(key)
