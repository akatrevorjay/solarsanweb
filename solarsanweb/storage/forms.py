
import logging
from dj import forms, User
from mongodbforms import DocumentForm

import storage.target

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Button, Row, Field
from crispy_forms.bootstrap import AppendedText, PrependedText, FormActions

from storage.models import Pool, Dataset, Volume, Filesystem, Snapshot
import storage.cache

from dj import reverse_lazy


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


class PoolCreateForm(BaseCreateForm):
    form_id = 'pool-create-form'
    form_action = reverse_lazy('pool-create')

    name = forms.CharField(
        initial='dpool',
        help_text=u'Simple name', )
    vdevs_left = forms.MultipleChoiceField(
        choices=(
            ("sda", "sda"),
            ("sdb", "sdb"),
            ("null", "Empty"),
        ),
        help_text=u'Disk devices to use', )
    vdevs_right = forms.MultipleChoiceField(
        choices=(
            ("sda", "sda"),
            ("sdb", "sdb"),
            ("null", "Empty"),
        ),
        help_text=u'Disk devices to use', )
    vdevs_types = forms.MultiValueField()

    def __init__(self, *args, **kwargs):
        super(PoolCreateForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Create Pool'))


DATASET_PARENT_CHOICES = ((x.name, x.name) for x in sorted(storage.cache.filesystems(), key=lambda x: x.name))


class BaseDatasetCreateForm(BaseCreateForm):
    parent = forms.ChoiceField(
        choices=DATASET_PARENT_CHOICES
    )
    name = forms.CharField()


class FilesystemCreateForm(BaseDatasetCreateForm):
    form_id = 'filesystem-create-form'
    form_action = reverse_lazy('filesystem-create')

    def __init__(self, *args, **kwargs):
        super(FilesystemCreateForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Create Filesystem'))


class VolumeCreateForm(BaseDatasetCreateForm):
    form_id = 'volume-create-form'
    form_action = reverse_lazy('volume-create')

    def __init__(self, *args, **kwargs):
        super(VolumeCreateForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Create Volume'))


TARGET_CHOICES = tuple((x.wwn, x.short_wwn()) for x in storage.cache.targets())
VOLUME_CHOICES = tuple((x.pk, x.name) for x in storage.cache.volumes())


class TargetPgVolumeLunMapForm(BaseCreateForm):
    volume = forms.ChoiceField(
        choices=VOLUME_CHOICES,
        help_text=u'Volume', )
    tpg_tag = forms.ChoiceField(
        choices=(
            ('1', 'tpg1'),
            #('2', 'tpg2'),
            #('3', 'tpg3'),
        ),
        help_text=u'Target Portal Group Tag', )
    lun = forms.ChoiceField(
        choices=(
            ('0', 'lun0'),
            #('1', 'lun1'),
            #('2', 'lun2'),
            #('3', 'lun3'),
        ),
        help_text=u'Lun', )

    def __init__(self, *args, **kwargs):
        super(TargetPgVolumeLunMapForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Map Volume to Lun'))


class VolumeTargetPgLunMappingCreateForm(BaseCreateForm):
    target_wwn = forms.ChoiceField(
        choices=TARGET_CHOICES,
        help_text=u'Target WWN', )
    tpg_tag = forms.ChoiceField(
        choices=(
            ('1', 'tpg1'),
            #('2', 'tpg2'),
            #('3', 'tpg3'),
        ),
        help_text=u'Target Portal Group Tag', )
    lun = forms.ChoiceField(
        choices=(
            ('0', 'lun0'),
            #('1', 'lun1'),
            #('2', 'lun2'),
            #('3', 'lun3'),
        ),
        help_text=u'Lun', )


class TargetCreateForm(BaseCreateForm):
    form_id = 'target-create-form'
    form_action = reverse_lazy('target-create')

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
    #target_wwn_auto = forms.ChoiceField(
    #    choices=(
    #        ("Automatic", "Generate one"),
    #        ("Manual", "Manual"), ), )
    #target_wwn = forms.CharField(
    #    max_length=100,
    #    initial='Automatic',
    #    help_text=u'WWN (unique identifier)', )

    def __init__(self, *args, **kwargs):
        super(TargetCreateForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Create Target'))


class TargetRefMixin(object):
    target_wwn = forms.ChoiceField(
        choices=TARGET_CHOICES,
        help_text=u'Target WWN (unique identifier)', )


class TargetRemoveForm(TargetRefMixin, BaseForm):
    form_id = 'target-remove-form'

    def __init__(self, *args, **kwargs):
        super(TargetRemoveForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Delete Target', css_class="btn-danger"))


class TargetPgMixin(object):
    tpg_tag = forms.IntegerField(
        help_text=u'Target Portal Group Tag (ID number)', )


class TargetPgCreateForm(TargetRefMixin, TargetPgMixin, BaseForm):
    enable = forms.BooleanField(
        help_text=u'Enabled', )


class TargetPgLunAclCreateForm(TargetPgMixin, BaseForm):
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


