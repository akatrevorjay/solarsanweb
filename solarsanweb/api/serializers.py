from django.forms import widgets
from rest_framework import serializers

from django.contrib.auth.models import User, Group, Permission
import storage.models


#class UserSerializer(serializers.HyperlinkedModelSerializer):
#    class Meta:
#        model = User
#        fields = ('url', 'username', 'email', 'groups')


class UserSerializer(serializers.ModelSerializer):
    #snippets = serializers.ManyPrimaryKeyRelatedField()
    snippets = serializers.ManyHyperlinkedRelatedField(view_name='snippet-detail')

    class Meta:
        model = User
        fields = ('id', 'username', 'snippets')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    permissions = serializers.ManySlugRelatedField(
        slug_field='codename',
        queryset=Permission.objects.all()
    )

    class Meta:
        model = Group
        fields = ('url', 'name', 'permissions')


class PoolSerializer(serializers.Serializer):
    pk = serializers.Field()  # Note: `Field` is an untyped read-only field.
    name = serializers.Field()
    guid = serializers.Field()
    #hostname = serializers.Field()
    #vdevs = serializers.Field()

    created = serializers.Field()
    modified = serializers.Field()

    def restore_object(self, attrs, instance=None):
        """Create or update a new snippet instance.
        """
        if instance:
            # Update existing instance
            #instance.name = attrs['name']
            return instance

        # Create new instance
        return storage.models.Pool(**attrs)

    ## Custom validation for 'title' field
    #def validate_title(self, attrs, source):
    #    """Check that the blog post is about Django.
    #    """
    #    value = attrs[source]
    #    if "django" not in value.lower():
    #        raise serializers.ValidationError("Blog post is not about Django")
    #    return attrs

    # Custom validation for all fields
    def validate(self, attrs):
        if self == 'nope':
            raise serializers.ValidationError
        return attrs



#class PoolSerializer(serializers.HyperlinkedModelSerializer):
#    class Meta:
#        model = storage.models.Pool
#        fields = ('name', )


class FilesystemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = storage.models.Filesystem
        fields = ('name', )


class VolumeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = storage.models.Volume
        fields = ('name', )


class SnapshotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = storage.models.Snapshot
        fields = ('name', )



#class RecipientSerializer(serializers.HyperlinkedModelSerializer):
#    class Meta:
#        model = models.Recipient
#        fields = ('email', 'phone')


#class RecipientGroupSerializer(serializers.HyperlinkedModelSerializer):
#    uuid = serializers.Field()

#    recipient_set = serializers.ManySlugRelatedField(
#        slug_field='email',
#        queryset=models.Recipient.objects.all(),
#        #widget=widgets.Textarea
#    )

#    class Meta:
#        model = models.RecipientGroup
#        fields = ('uuid', 'name', 'recipient_set')


#class TemplateSerializer(serializers.HyperlinkedModelSerializer):
#    uuid = serializers.Field()
#    slug = serializers.Field()
#    created = serializers.Field()
#    modified = serializers.Field()

#    class Meta:
#        model = models.Template
#        #fields = ('uuid', 'subject', 'template', 'context')
#        exclude = ('id', )


#class CampaignSerializer(serializers.HyperlinkedModelSerializer):
#    uuid = serializers.Field()
#    slug = serializers.Field()
#    recipient_index = serializers.Field()
#    created = serializers.Field()
#    modified = serializers.Field()

#    #status = serializers.HyperlinkedIdentityField(view_name='campaign-status', format='html')
#    #start = serializers.HyperlinkedIdentityField(view_name='campaign-start', format='html')
#    #pause = serializers.HyperlinkedIdentityField(view_name='campaign-pause', format='html')

#    #recipient_group = serializers.SlugRelatedField(
#    #    slug_field='name',
#    #    queryset=models.RecipientGroup.objects.all(),
#    #)
#    recipient_group = serializers.HyperlinkedRelatedField(view_name='recipient_group-detail',
#                                                          slug_field='name')
#    #recipient_group = RecipientGroupSerializer()

#    #template = serializers.SlugRelatedField(
#    #    slug_field='name',
#    #    queryset=models.Template.objects.all(),
#    #)
#    template = serializers.HyperlinkedRelatedField(view_name='template-detail',
#                                                   slug_field='name')
#    #template = TemplateSerializer()

#    class Meta:
#        model = models.Campaign
#        #fields = ('uuid', 'subject', 'template', 'recipient_group', 'sender', 'template', 'context')
#        exclude = ('id', )
#        depth = 1


#
# restframework examples
#


#
# Custom serializer field
#

class Color(object):
    """A color represented in the RGB colorspace.
    """
    def __init__(self, red, green, blue):
        assert(red >= 0 and green >= 0 and blue >= 0)
        assert(red < 256 and green < 256 and blue < 256)
        self.red, self.green, self.blue = red, green, blue


class ColourField(serializers.WritableField):
    """Color objects are serialized into "rgb(#, #, #)" notation.
    """
    def to_native(self, obj):
        return "rgb(%d, %d, %d)" % (obj.red, obj.green, obj.blue)

    def from_native(self, data):
        data = data.strip('rgb(').rstrip(')')
        red, green, blue = [int(col) for col in data.split(',')]
        return Color(red, green, blue)


class ClassNameField(serializers.WritableField):
    def field_to_native(self, obj, field_name):
        """Serialize the object's class name, not an attribute of the object.
        """
        return obj.__class__.__name__

    def field_from_native(self, data, field_name, into):
        """We don't want to set anything when we revert this field.
        """
        pass


#class SnippetSerializerNonModel(serializers.Serializer):
#    pk = serializers.Field()  # Note: `Field` is an untyped read-only field.
#    title = serializers.CharField(required=False,
#                                  max_length=100)
#    code = serializers.CharField(widget=widgets.Textarea,
#                                 max_length=100000)
#    linenos = serializers.BooleanField(required=False)
#    language = serializers.ChoiceField(choices=models.LANGUAGE_CHOICES,
#                                       default='python')
#    style = serializers.ChoiceField(choices=models.STYLE_CHOICES,
#                                    default='friendly')

#    def restore_object(self, attrs, instance=None):
#        """Create or update a new snippet instance.
#        """
#        if instance:
#            # Update existing instance
#            instance.title = attrs['title']
#            instance.code = attrs['code']
#            instance.linenos = attrs['linenos']
#            instance.language = attrs['language']
#            instance.style = attrs['style']
#            return instance

#        # Create new instance
#        return models.Snippet(**attrs)

#    # Custom validation for 'title' field
#    def validate_title(self, attrs, source):
#        """Check that the blog post is about Django.
#        """
#        value = attrs[source]
#        if "django" not in value.lower():
#            raise serializers.ValidationError("Blog post is not about Django")
#        return attrs

#    # Custom validation for all fields
#    def validate(self, attrs):
#        if self == 'nope':
#            raise serializers.ValidationError
#        return attrs


#class SnippetSerializer(serializers.HyperlinkedModelSerializer):
#    owner = serializers.Field(source='owner.username')
#    highlight = serializers.HyperlinkedIdentityField(view_name='snippet-highlight', format='html')

#    class Meta:
#        model = models.Snippet
#        fields = ('url', 'highlight', 'owner',
#                  'title', 'code', 'linenos', 'language', 'style')



