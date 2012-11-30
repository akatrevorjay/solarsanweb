
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


"""
Bases
"""

class BaseForm(forms.Form):
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

        return super(BaseForm, self).__init__(*args, **kwargs)


class BaseCreateForm(BaseForm):
    #form_class = 'form-horizontal'
    form_class = 'form-inline'

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        return super(BaseCreateForm, self).__init__(*args, **kwargs)

    def save(self):
        pass


"""
Login
"""


class LoginForm(BaseForm):
    username = forms.CharField()
    password = forms.PasswordInput()

    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Add'))


