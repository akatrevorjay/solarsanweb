
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
from storage.models import Pool, Dataset, Volume, Filesystem, Snapshot
from storage.device import Drives, Devices
import storage.cache
import storage.target

import rtslib



"""
Devices
"""


def _populate_drives_choices():
    ret = []
    # TODO Check that device is not in use already
    for d in sorted(Drives.filter(), key=lambda x: x.path_by_id()):
        path_by_id = d.path_by_id()
        basepath = os.path.basename(path_by_id)
        if basepath.startswith('zd') or d.is_removable:
            continue

        name = [basepath]
        for k, v in {'label':  d.is_partitioned,
                     'rot':    d.is_rotational,
                     }.items():
            if v:
                name.append(k)
        name = '; '.join(name)

        ret.append((path_by_id, name))
    return ret

DRIVES_CHOICES = _populate_drives_choices()


class DeviceForm(BaseCreateForm):
    paths = forms.MultipleChoiceField(
        choices=DRIVES_CHOICES,
        help_text=u'Select which connected storage devices to use for this mirrored/fault tolerant unit.', )

    use_as = forms.ChoiceField(
        choices=(
            ('data', 'Data'),
            #(If a storage device in a mirrored set shows signs of near-failure or fails, if a spare is available, automatically initiate disk replacement.)', 'spare'),
            ('spare', 'Spare'),
            ('cache', 'Cache'),
            ('journal', 'Journal'),
        ),
        help_text=u'Data adds to available space. Spares are used for initiating auto-replacement of a marked near-fail/failed device in a mirrored set.',
        #Cache and Journal are for performance and require very selective non-rotational media to operate correctly. We always install a hefty amount stock. very high-speed non-rotational media that has been installed and verified up-to-par at factory to ensure data reliability. Journal needs to be a redundant mirrored set as well.',
    )

    #def __init__(self, *args, **kwargs):
    #    super(DeviceSetForm, self).__init__(*args, **kwargs)
    #    self.helper.add_input(Submit('submit', 'Done'))


class BaseDeviceFormSet(BaseFormSet):
    def clean(self):
        """Checks that no two devices are the same."""
        if any(self.errors) or self.total_form_count() < 1:
            # Don't bother validating the formset unless each form is valid on its own
            return

        paths = []
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            form_paths = form.cleaned_data['paths']
            for path in form_paths:
                if path in paths:
                    raise forms.ValidationError("Devices cannot be used multiple times.")
            titles.append(title)


DeviceFormSet = formset_factory(
    DeviceForm,
    formset=BaseDeviceFormSet,
    #can_order=True,
    can_delete=True,
    #extra=2,
)


#class ExampleBaseArticleFormSet(BaseFormSet):
#    def clean(self):
#        """Checks that no two articles have the same title."""
#        if any(self.errors):
#            # Don't bother validating the formset unless each form is valid on its own
#            return
#        titles = []
#        for i in range(0, self.total_form_count()):
#            form = self.forms[i]
#            title = form.cleaned_data['title']
#            if title in titles:
#                raise forms.ValidationError("Articles in a set must have distinct titles.")
#            titles.append(title)
#
#    def add_fields(self, form, index):
#        super(ExampleBaseArticleFormSet, self).add_fields(form, index)
#        form.fields["my_field"] = forms.CharField()


"""
Pools
"""


class PoolCreateInitialForm(BaseCreateForm):
    form_id = 'pool-create-form'
    form_action = reverse_lazy('pool-create')

    name = forms.CharField(
        #initial='dpool',
        help_text=u'Simple name', )

    redundancy_type = forms.ChoiceField(
        choices=(
            # Recommended, IOPs, Read,Write=Fast, Failure Tolerance:
            # <mirrorCount>, 100%/<mirrorCount> usable)
            ("1+0", "Striped over mirrored sets [1+0]"),

            # Decent Read, Slow Write, 3*Redundant, 2*Redundant N-2 usable)
            #("6", "Parity with two layers of failure tolerance [6]"),
        ),
        help_text=u'Similar to "raid level".', )

    #def __init__(self, *args, **kwargs):
    #    super(PoolCreateInitialForm, self).__init__(*args, **kwargs)
    #    #self.helper.add_input(Submit('submit', 'Create Pool'))


DATASET_PARENT_CHOICES = ((x.name, x.name) for x in sorted(storage.cache.filesystems(), key=lambda x: x.name))


class BaseDatasetCreateForm(BaseCreateForm):
    parent = forms.ChoiceField(
        choices=DATASET_PARENT_CHOICES
    )
    # TODO Validation against these to make sure they are merely [\w\d]
    # seperated by forward slashes
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

    size = forms.CharField(
        help_text=u'Amount of space to designate to the volume. Suffixes are supported, ie 2T, 100G.', )

    def __init__(self, *args, **kwargs):
        super(VolumeCreateForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Create Volume'))


TARGET_CHOICES = tuple((x.wwn, x.short_wwn()) for x in storage.cache.targets())
VOLUME_CHOICES = tuple((x.pk, x.name) for x in storage.cache.volumes())


class VolumeLunMapInitialForm(BaseCreateForm):
    target_wwn = forms.ChoiceField(
        choices=TARGET_CHOICES,
        help_text=u'Identifier of existing target.', )


# FIXME Generate choices list, but this should be gotten via ajax
LUN_CHOICES = []
for x in xrange(0, 9):
    LUN_CHOICES.append(('%d' % x, 'lun%d' % x))


class LunForm(BaseCreateForm):
    lun = forms.ChoiceField(
        choices=LUN_CHOICES,
        help_text=u'Logical Unit Number', )

    def __init__(self, *args, **kwargs):
        super(LunForm, self).__init__(*args, **kwargs)
        #luns = LUN_CHOICES
        #self.fields['lun'].choices.extend(luns)


class LunCreateForm(LunForm):
    volume = forms.ChoiceField(
        choices=VOLUME_CHOICES,
        help_text=u'Volume to map to Lun', )

    def __init__(self, *args, **kwargs):
        super(LunCreateForm, self).__init__(*args, **kwargs)

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Add'))


class PortalCreateForm(BaseCreateForm):
    ip = forms.CharField(
        initial='0.0.0.0',
        help_text=u'Bind to this IP address', )
    port = forms.IntegerField(
        initial=3260,
        help_text=u'Bind to this port', )

    def __init__(self, *args, **kwargs):
        super(PortalCreateForm, self).__init__(*args, **kwargs)

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Add'))


class AclCreateForm(BaseCreateForm):
    node_wwn = forms.CharField(
        help_text=u'Node WWN to create ACL for', )

    def __init__(self, *args, **kwargs):
        super(AclCreateForm, self).__init__(*args, **kwargs)

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Add'))


class ConfirmForm(BaseCreateForm):
    confirm = forms.BooleanField(
            initial=False,
            help_text=u'Are you sure?', )

    def __init__(self, *args, **kwargs):
        super(ConfirmForm, self).__init__(*args, **kwargs)

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Confirm'))


# FIXME Generate choices list, but this should be gotten via ajax
TPG_TAG_CHOICES = []
for x in xrange(1, 10):
    TPG_TAG_CHOICES.append(('%d' % x, 'tpg%d' % x))


class TpgForm(BaseCreateForm):
    tag = forms.ChoiceField(
        choices=TPG_TAG_CHOICES,
        help_text=u'Portal Group Tag', )

    def __init__(self, *args, **kwargs):
        super(TpgForm, self).__init__(*args, **kwargs)

        # TODO Only show available tpg tags
        #tags = TPG_TAG_CHOICES
        #self.fields['tag'].choices.extend(tags)


class TpgCreateForm(BaseCreateForm):
    def __init__(self, *args, **kwargs):
        super(TpgCreateForm, self).__init__(*args, **kwargs)

        # TODO Fix this so the modal Save Changes button works instead
        self.helper.add_input(Submit('submit', 'Add'))


class AjaxTpgUpdateForm(Form):
    enable = forms.IntegerField()


class TpgVolumeLunMapForm(TpgForm, LunForm):
    volume = forms.ChoiceField(
        choices=VOLUME_CHOICES,
        help_text=u'Volume', )

    def __init__(self, *args, **kwargs):
        super(TpgVolumeLunMapForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Map Volume to Lun'))


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


class TargetDeleteForm(TargetRefMixin, BaseForm):
    form_id = 'target-remove-form'

    def __init__(self, *args, **kwargs):
        super(TargetDeleteForm, self).__init__(*args, **kwargs)
        self.helper.add_input(Submit('submit', 'Delete Target', css_class="btn-danger"))


class TpgMixin(object):
    tag = forms.IntegerField(
        help_text=u'Target Portal Group Tag (ID number)', )


#class TpgCreateForm(TargetRefMixin, TpgMixin, BaseForm):
#    enable = forms.BooleanField(
#        help_text=u'Enabled', )


class TpgLunAclCreateForm(TpgMixin, BaseForm):
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
        super(TpgLunAclCreateForm, self).__init__(*args, **kwargs)




'''
class MessageForm(Form):
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
'''
