from tastypie import authorization
from tastypie_mongoengine import resources, fields
from .models import Pool, VDevDisk


class VDevDiskResource(resources.MongoEngineResource):
    class Meta:
        object_class = VDevDisk


class PoolResource(resources.MongoEngineResource):
    class Meta:
        #queryset = Pool.objects.all()
        object_class = Pool
        allowed_methods = ('get', 'post', 'put', 'delete')
        authorization = authorization.Authorization()
    #customer = fields.EmbeddedDocumentField(embedded='test_project.test_app.api.resources.EmbeddedPersonResource', attribute='customer')
    #vdevs = fields.EmbeddedListField(of='test_project.test_app.api.resources.EmbeddedPersonResource', attribute='embeddedlist', full=True)
    vdevs = fields.EmbeddedListField(of='storage.api.VDevDiskResource', attribute='vdevs')


"""
class EmbeddedPersonResource(resources.MongoEngineResource):
    class Meta:
        object_class = documents.EmbeddedPerson


class CustomerResource(resources.MongoEngineResource):
    person = fields.ReferenceField(to='test_project.test_app.api.resources.PersonResource', attribute='person', full=True)


class EmbeddedDocumentFieldTestResource(resources.MongoEngineResource):
    customer = fields.EmbeddedDocumentField(embedded='test_project.test_app.api.resources.EmbeddedPersonResource', attribute='customer')



class EmbeddedListFieldTestResource(resources.MongoEngineResource):
    embeddedlist = fields.EmbeddedListField(of='test_project.test_app.api.resources.EmbeddedPersonResource', attribute='embeddedlist', full=True)

# EmbeddedListField also exposes its embedded documents as subresources, so you can access
# them directly. For example, URI of the first element of the list above could be
# /api/v1/embeddedlistfieldtest/4fb88d7549902817fe000000/embeddedlist/0/. You can also
# manipulate subresources in the same manner as resources themselves.



## MODELS
class Person(mongoengine.Document):
    meta = {
        'allow_inheritance': True,
    }

    name = mongoengine.StringField(max_length=200, required=True)
    optional = mongoengine.StringField(max_length=200, required=False)

class StrangePerson(Person):
    strange = mongoengine.StringField(max_length=100, required=True)

## ^^ MODELS RESOURCES LINKED; POLYMORPHISM
class StrangePersonResource(resources.MongoEngineResource):
    class Meta:
        queryset = documents.StrangePerson.objects.all()

class PersonResource(resources.MongoEngineResource):
    class Meta:
        queryset = documents.Person.objects.all()
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        authorization = authorization.Authorization()

        polymorphic = {
            'person': 'self',
            'strangeperson': StrangePersonResource,
        }
"""
