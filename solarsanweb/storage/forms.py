
import logging
from dj import forms, User
from mongodbforms import DocumentForm

import storage.target

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions

from storage.models import Pool, Dataset, Volume, Filesystem, Snapshot
import storage.cache


class VolumeCreateForm(forms.Form):
    name = forms.CharField()
    #parent = referencefield mongo somehow

class TargetCreateForm(forms.Form):
    fabric_module = forms.ChoiceField(
        #widget = forms.RadioSelect,
        choices=(
            ("iscsi", "iSCSI"),
            #("ib_srpt", "SRP"),
            #("iser", "iSER"),
            #("fc", "Fibre Channel"),
        ),
        initial = "iSCSI",
        help_text=u"iSCSI is easy to maintain and use"
    )

    # For now all WWNs are automatic
    #wwn_auto = forms.ChoiceField(
    #    choices=(
    #        ("Automatic", "Generate one"),
    #        ("Manual", "Manual"), ), )
    #wwn = forms.CharField(
    #    max_length=100,
    #    initial='Automatic',
    #    help_text=u'WWN (unique identifier)', )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        self.helper.form_action = 'submit_survey'

        self.helper.add_input(Submit('submit', 'Create Target'))

        # oddness
        self.instance = kwargs.pop('instance', None)

        return super(TargetCreateForm, self).__init__(*args, **kwargs)

    def dumps(self):
        logging.debug('Creating Target instance=%s, form=%s', self.instance, self.__dict__)

class TargetRefMixin(object):
    target_wwn = forms.MultipleChoiceField(
        choices = (x.wwn for x in storage.cache.targets()),
        help_text=u'Target WWN (unique identifier)', )

class TargetPgMixin(object):
    tpg_tag = forms.IntegerField(
        help_text=u'Target Portal Group Tag (ID number)', )

class TargetPgCreateForm(TargetRefMixin, TargetPgMixin, forms.Form):
    enable = forms.BooleanField(
        help_text=u'Enabled', )

class TargetPgLunAclCreateForm(TargetPgMixin, forms.Form):
    allowed_wwns = forms.CharField(
        widget = forms.Textarea(),
        help_text=u'Allowed WWNs' )
    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_id = 'id-exampleForm'
        self.helper.form_class = 'blueForms'
        self.helper.form_method = 'post'
        self.helper.form_action = 'submit_survey'

        self.helper.add_input(Submit('submit', 'Submit'))
        super(TargetPgLunAclCreateForm, self).__init__(*args, **kwargs)

class AjaxTargetPgUpdateForm(forms.Form):
    enable = forms.IntegerField()




class MessageForm(forms.Form):
    text_input = forms.CharField()

    textarea = forms.CharField(
        widget = forms.Textarea(),
    )

    radio_buttons = forms.ChoiceField(
        choices = (
            ('option_one', "Option one is this and that be sure to include why it's great"),
            ('option_two', "Option two can is something else and selecting it will deselect option one")
        ),
        widget = forms.RadioSelect,
        initial = 'option_two',
    )

    checkboxes = forms.MultipleChoiceField(
        choices = (
            ('option_one', "Option one is this and that be sure to include why it's great"),
            ('option_two', 'Option two can also be checked and included in form results'),
            ('option_three', 'Option three can yes, you guessed it also be checked and included in form results')
        ),
        initial = 'option_one',
        widget = forms.CheckboxSelectMultiple,
        help_text = "<strong>Note:</strong> Labels surround all the options for much larger click areas and a more usable form.",
    )

    appended_text = forms.CharField(
        help_text = "Here's more help text"
    )

    prepended_text = forms.CharField()

    prepended_text_two = forms.CharField()

    multicolon_select = forms.MultipleChoiceField(
        choices = (('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')),
    )

    # Uni-form
    helper = FormHelper()
    helper.form_class = 'form-horizontal'
    helper.layout = Layout(
        Field('text_input', css_class='input-xlarge'),
        Field('textarea', rows="3", css_class='input-xlarge'),
        'radio_buttons',
        Field('checkboxes', style="background: #FAFAFA; padding: 10px;"),
        AppendedText('appended_text', '.00'),
        PrependedText('prepended_text', '<input type="checkbox" checked="checked" value="" id="" name="">', active=True),
        PrependedText('prepended_text_two', '@'),
        'multicolon_select',
        FormActions(
            Submit('save_changes', 'Save changes', css_class="btn-primary"),
            Submit('cancel', 'Cancel'),
        )
    )

""" Template code for above:
    {% extends 'base.html' %}
    {% load crispy_forms_tags %}

{% block content %}
{% crispy form %}
{% endblock %}
"""


