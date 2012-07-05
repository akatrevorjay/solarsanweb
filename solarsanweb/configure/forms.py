from django.forms import ModelForm

from models import NetworkInterfaceConfig

class NetworkInterfaceConfigForm(ModelForm):
    class Meta:
        model = NetworkInterfaceConfig
        exclude = ('last_modified', 'created',)

class Config(ModelForm):
    class Meta:
        model = Config
        exclude = ('last_modified', 'created',)


#class ContactForm(forms.Form):
#    name = forms.CharField()
#    message = forms.CharField(widget=forms.Textarea)
#
#    def send_email(self):
#        # send email using the self.cleaned_data dictionary
#        pass


