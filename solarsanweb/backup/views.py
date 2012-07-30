from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from django_mongokit import get_database, connection
from storage.models import zPool, zDataset

from storage.models import Pool, Dataset, Filesystem, Snapshot
import zfs


