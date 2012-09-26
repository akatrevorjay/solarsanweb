# forms.py
from django import forms
#from models import NetworkInterfaceConfig, ConfigEntry
import models

from django_mongoengine.forms import EmbeddedDocumentForm

#class CommentForm(EmbeddedDocumentForm):

#    class Meta:
#        document = Comment
#        embedded_field_name = 'comments'
#        exclude = ('created_at',)



class NetworkInterfaceForm(EmbeddedDocumentForm):
    class Meta:
        document = models.NetworkInterface
        #exclude = ('name', 'created', 'modified')


#class ConfigEntry(forms.ModelForm):
#    class Meta:
#        model = models.Config
#        exclude = ('last_modified', 'created',)


#class ContactForm(forms.Form):
#    name = forms.CharField()
#    message = forms.CharField(widget=forms.Textarea)
#
#    def send_email(self):
#        # send email using the self.cleaned_data dictionary
#        pass


