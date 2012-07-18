
import random


class MongoRouter(object):
    """A router to control all database operations on models in
    the myapp application"""
    db_name = 'mongodb'
    supported_db_tables = ['blog_posts', 'blog_posts_tags', 'api_user', 'api_user_profile', 'socialize_application',
                           'socialize_comment', 'socialize_entity', 'socialize_like',
                           'socialize_share', 'socialize_medium', 'socialize_view']

    def is_supported(self, model):
        #print  model._meta.db_table
        return model._meta.db_table in self.supported_db_tables

    def db_for_read(self, model, **hints):
        "Point all operations on supported models to 'other'"
        if self.is_supported(model):
            return self.db_name
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on myapp models to 'other'"
        if self.is_supported(model):
            return self.db_name
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in myapp is involved"
        if obj1._meta.app_label == 'myapp' or obj2._meta.app_label == 'myapp':
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the myapp app only appears on the 'other' db"
        if db == self.db_name:
            return self.is_supported(model)
        elif self.is_supported(model):
            return False
        return None


class DatabaseRouter(object):
    """A router to control all database operations on models in
    the myapp application"""

    def db_for_read(self, model, **hints):
        "Point all operations on myapp models to 'other'"
        if model._meta.app_label == 'django_mongodb_cache':
            return 'other'
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on myapp models to 'other'"
        if model._meta.app_label == 'myapp':
            return 'other'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in myapp is involved"
        if obj1._meta.app_label == 'myapp' or obj2._meta.app_label == 'myapp':
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the myapp app only appears on the 'other' db"
        if db == 'other':
            return model._meta.app_label == 'myapp'
        elif model._meta.app_label == 'myapp':
            return False
        return None


class ModelMetaRouter(object):
    def db_for_read(self, model, **hints):
        # TODO This shouldn't be hard coded here.
        if model in ['django_mongodb_cache']:
            return 'mongodb'
        return getattr(model._meta, 'using', None)

    def db_for_write(self, model, **hints):
        return getattr(model._meta, 'using', None)

    def allow_relation(self, obj1, obj2, **hints):
        # only allow relations within a single database
        if getattr(obj1._meta, 'using', None) == getattr(obj2._meta, 'using', None):
            return True
        return None

    def allow_syncdb(self, db, model):
        if db == getattr(model._meta, 'using', 'default'):
            return True
        return None


class MasterSlaveRouter(object):
    """A router that sets up a simple master/slave configuration"""

    def db_for_read(self, model, **hints):
        "Point all read operations to a random slave"
        return random.choice(['slave1','slave2'])

    def db_for_write(self, model, **hints):
        "Point all write operations to the master"
        return 'master'

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation between two objects in the db pool"
        db_list = ('master','slave1','slave2')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_syncdb(self, db, model):
        "Explicitly put all models on all databases."
        return True


