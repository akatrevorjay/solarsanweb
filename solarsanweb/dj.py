
from django.views import generic
from django import http
from django.shortcuts import *

from django.http import HttpResponseRedirect
from django.shortcuts import render, render_to_response, get_object_or_404

from django.template import RequestContext

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django import forms
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.urlresolvers import reverse, resolve, is_valid_path, iri_to_uri

