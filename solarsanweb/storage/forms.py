
import logging
from django import forms
from mongodbforms import DocumentForm

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)

import storage.target

class TargetForm(forms.Form):
    wwn = forms.CharField()

class TargetTPGForm(forms.Form):
    target_wwn = forms.CharField()
    tag = forms.IntegerField()
    enable = forms.IntegerField()

    def save(self, **kwargs):
        data = self.cleaned_data
        target = storage.target.get(data['target_wwn'])

        #tpg = list(target.tpgs)[data['tag'] - 1]
        for x in target.tpgs:
            if x.tag == data['tag']:
                tpg = x
                break

        logging.debug('save data=%s', data)

        if data['enable']:
            tpg.enable = 1
        else:
            tpg.enable = 0

