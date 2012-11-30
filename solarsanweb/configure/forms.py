
import os
import logging
from dj import forms, formsets, formset_factory, \
               Form, BaseFormSet, \
               User, \
               reverse_lazy
from mongodbforms import DocumentForm

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions

from solarsan.forms import BaseForm, BaseCreateForm

import configure.models


class NetworkInterfaceForm(DocumentForm):
    class Meta:
        document = configure.models.NetworkInterface
        #exclude = ('name', 'created', 'modified')

    form_id = None
    form_class = None
    form_method = 'post'
    form_action = None
    help_text_inline = None

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        if self.form_id:
            self.helper.form_id = self.form_id
        if self.form_class:
            self.helper.form_class = self.form_class
        if self.form_method:
            self.helper.form_method = self.form_method
        if self.form_action:
            self.helper.form_action = self.form_action
        if self.help_text_inline:
            self.helper.help_text_inline = self.help_text_inline

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Save'))
        return super(NetworkInterfaceForm, self).__init__(*args, **kwargs)



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


