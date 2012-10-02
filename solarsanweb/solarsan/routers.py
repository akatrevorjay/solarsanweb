
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import random

_mongodbs = []


def _init_mongodbs():
    for name, options in settings.DATABASES.iteritems():
        #if options['ENGINE'] != 'django_mongodb_engine':
        if options['ENGINE'] != 'django_mongokit.mongodb':
            continue
        if options.get('IS_DEFAULT'):
            _mongodbs.insert(0, name)
        else:
            _mongodbs.append(name)

    if not _mongodbs:
        raise ImproperlyConfigured("No MongoDB database found in "
                                   "settings.DATABASES.")


class MongoDBRouter(object):
    """
    A Django router to manage models that should be stored in MongoDB.

    MongoDBRouter uses the MONGODB_MANAGED_APPS and MONGODB_MANAGED_MODELS
    settings to know which models/apps should be stored inside MongoDB.

    See: http://docs.djangoproject.com/en/dev/topics/db/multi-db/#topics-db-multi-db-routing
    """
    init_error = None
    managed_apps = []
    managed_models = []

    def __init__(self):
        if not _mongodbs:
            try:
                _init_mongodbs()
            except ImproperlyConfigured:
                self.init_error = True

        self.managed_apps.extend([app.split('.')[-1] for app in
                             getattr(settings, 'MONGODB_MANAGED_APPS', [])])
        self.managed_models.extend(getattr(settings, 'MONGODB_MANAGED_MODELS', []))

    def is_managed(self, model):
        """
        Returns True if the model passed is managed by Django MongoDB
        Engine.
        """
        if model._meta.app_label in self.managed_apps:
            return True
        full_name = '%s.%s' % (model._meta.app_label, model._meta.object_name)
        return full_name in self.managed_models

    def db_for_read(self, model, **hints):
        """
        Points all operations on MongoDB models to a MongoDB database.
        """
        if self.is_managed(model):
            return _mongodbs[0]

    db_for_write = db_for_read  # Same algorithm.

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allows any relation if a model in myapp is involved.
        """
        return self.is_managed(obj2) or None

    def allow_syncdb(self, db, model):
        """
        Makes sure that MongoDB models only appear on MongoDB databases.
        """
        if db in _mongodbs:
            return self.is_managed(model)
        elif self.is_managed(model):
            return db in _mongodbs
        return None


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
        return random.choice(['slave1', 'slave2'])

    def db_for_write(self, model, **hints):
        "Point all write operations to the master"
        return 'master'

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation between two objects in the db pool"
        db_list = ('master', 'slave1', 'slave2')
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_syncdb(self, db, model):
        "Explicitly put all models on all databases."
        return True


