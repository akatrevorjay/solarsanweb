# forms.py
from django import forms
#from models import NetworkInterfaceConfig, ConfigEntry
import models


class NetworkInterfaceConfigForm(forms.ModelForm):
    class Meta:
        model = models.NetworkInterfaceConfig
        exclude = ('name', 'last_modified', 'created',)


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


