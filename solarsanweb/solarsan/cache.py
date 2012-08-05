
from django_mongodb_cache import MongoDBCache

class EasyGoingMongoDBCache(MongoDBCache):
    """ Override's MongoDBCache to be able to have keys with '.' and '$', hackily. """
    def _clean_key(self, key):
        if key:
            if '.' in key: key = key.replace('.', '<dot>')
            if '$' in key: key = key.replace('$', '<gmoney>')
        return key
    def get(self, key, default=None, version=None, raw=False, raw_key=False):
        return super(EasyGoingMongoDBCache, self).get(self._clean_key(key), default, version, raw, raw_key)
    def set(self, key, value, timeout=None, version=None):
        return super(EasyGoingMongoDBCache, self).set(self._clean_key(key), value, timeout, version)

