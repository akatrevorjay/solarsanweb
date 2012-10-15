
#import zfs
import zfs.objects
import mongoengine as m
from . import BaseMixIn


"""
Property
"""


class PropertyDocument(BaseMixIn, m.EmbeddedDocument, zfs.objects.Property):
    meta = {'abstract': True, }
    name = m.StringField(required=True, unique=True)
    value = m.StringField()
    source = m.StringField()
    #created = m.DateTimeField(default=datetime.now())
    ## TODO Override validation and ensure modified gets updated on modification
    #modified = m.DateTimeField(default=datetime.now())

    def __repr__(self):
        prefix = ''
        source = ''
        if self.source == '-':
            prefix += 'Statistic'
        elif self.source in ['default', 'local', 'received']:
            prefix += self.source.capitalize()
        elif self.source:
            prefix += 'Inherited'
            source = ' source=%s' % self.source

        #if self.modified:
        #    prefix += 'Unsaved'

        name = prefix + self.__class__.__name__
        return "%s(%s=%s%s)" % (name, self.name, self.value, source)

    def __unicode__(self):
        return unicode(self.value)

    def __str__(self):
        return str(self.value)

    def __nonzero__(self):
        value = self.value
        if value == 'on':
            return True
        elif value:
            return False

    def __call__(self):
        return self.__unicode__()


class Property(PropertyDocument):
    pass
