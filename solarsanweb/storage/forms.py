
import logging
from dj import forms, User
from mongodbforms import DocumentForm
from bootstrap_toolkit.widgets import BootstrapDateInput

import storage.target


class TestForm(forms.Form):
    title = forms.CharField(
        max_length=100,
        help_text=u'This is the standard text input',
    )
    disabled = forms.CharField(
        max_length=100,
        help_text=u'I am read only',
        widget=forms.TextInput(attrs={
            'disabled': 'disabled'
        })
    )
    content = forms.ChoiceField(
        choices=(
            ("text", "Plain text"),
            ("html", "HTML"),
        ),
        help_text=u'Pick your choice',
    )
    email = forms.EmailField()
    like = forms.BooleanField(required=False)
    fruits = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        choices=(
            ("apple", "Apple"),
            ("pear", "Pear"),
        ),
        help_text=u'As you can see, multiple checkboxes work too',
    )
    veggies = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple(attrs={
            'inline': True,
        }),
        choices=(
            ("broccoli", "Broccoli"),
            ("carrots", "Carrots"),
            ("turnips", "Turnips"),
        ),
        help_text=u'And can be inline',
    )
    color = forms.ChoiceField(
        widget=forms.RadioSelect,
        choices=(
            ("#f00", "red"),
            ("#0f0", "green"),
            ("#00f", "blue"),
        ),
        help_text=u'And we have <i>radiosets</i>',
    )

    def clean(self):
        cleaned_data = super(TestForm, self).clean()
        raise forms.ValidationError("This error was added to show the non field errors styling.")
        return cleaned_data


class TestModelForm(forms.ModelForm):
    class Meta:
        model = User


class TestInlineForm(forms.Form):
    query = forms.CharField(required=False, label="")
    active = forms.ChoiceField(widget=forms.RadioSelect, label="", choices=(
        ('all', 'all'),
        ('active', 'active'),
        ('inactive', 'inactive')
        ), initial='all')
    mine = forms.BooleanField(required=False, label='Mine only', initial=False)


class WidgetsForm(forms.Form):
    date = forms.DateField(widget=BootstrapDateInput)



from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions


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

class TargetCreateForm(forms.Form):
    wwn = forms.CharField()

    # TODO Once this is saved, don't allow modifications
    fabric_module_name = forms.ChoiceField(
        choices=(
            ("iscsi", "ISCSI Target"),
            ("srp", "Infiniband SRP Target"),
        ),
        help_text=u'Select the fabric you wish to use. SRP really screams performance while iSCSI is easy to use/maintain.'
    )


class TargetPortalGroupCreateForm(forms.Form):
    target_wwn = forms.CharField(
        max_length=100,
        help_text=u'WWN (unique identifier)', )
    tag = forms.IntegerField(
        help_text=u'Target Portal Group Tag (ID number)', )
    enable = forms.BooleanField(
        help_text=u'Enabled', )


class TargetPortalGroupUpdateForm(forms.Form):
    enable = forms.IntegerField()


class TargetPortalGroupLunAcl(forms.Form):
    pass
