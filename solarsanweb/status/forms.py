
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


"""
Reboot
"""


class RebootForm(BaseForm):
    def __init__(self, *args, **kwargs):
        super(RebootForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Confirm'))
