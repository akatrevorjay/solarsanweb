
from piston.handler import BaseHandler
from piston.utils import rc, throttle

#from django_mongokit import get_database, connection
#from configure.models import ClusterNode, NetworkInterfaceList
#from django.conf import settings

#from myapp.models import Blogpost
#
#class BlogPostHandler(BaseHandler):
#    allowed_methods = ('GET', 'PUT', 'DELETE')
#    fields = ('title', 'content', ('author', ('username', 'first_name')), 'content_size')
#    exclude = ('id', re.compile(r'^private_'))
#    model = Blogpost
#
#    @classmethod
#    def content_size(self, blogpost):
#        return len(blogpost.content)
#
#    def read(self, request, post_slug):
#        post = Blogpost.objects.get(slug=post_slug)
#        return post
#
#    @throttle(5, 10*60) # allow 5 times in 10 minutes
#    def update(self, request, post_slug):
#        post = Blogpost.objects.get(slug=post_slug)
#
#        post.title = request.PUT.get('title')
#        post.save()
#
#        return post
#
#    def delete(self, request, post_slug):
#        post = Blogpost.objects.get(slug=post_slug)
#
#        if not request.user == post.author:
#            return rc.FORBIDDEN # returns HTTP 401
#
#        post.delete()
#
#        return rc.DELETED # returns HTTP 204
#
#class ArbitraryDataHandler(BaseHandler):
#    methods_allowed = ('GET',)
#
#    def read(self, request, username, data):
#        user = User.objects.get(username=username)
#
#        return { 'user': user, 'data_length': len(data) }

#class BlogPostHandler(BaseHandler):
#    allowed_methods = ('GET', 'PUT', 'DELETE')
#    fields = ('title', 'content', ('author', ('username', 'first_name')), 'content_size')
#    exclude = ('id', re.compile(r'^private_'))
#    model = Blogpost
#
#    @classmethod
#    def content_size(self, blogpost):
#        return len(blogpost.content)
#
#    def read(self, request, post_slug):
#        post = Blogpost.objects.get(slug=post_slug)
#        return post
#
#    @throttle(5, 10*60) # allow 5 times in 10 minutes
#    def update(self, request, post_slug):
#        post = Blogpost.objects.get(slug=post_slug)
#
#        post.title = request.PUT.get('title')
#        post.save()
#
#        return post
#
#    def delete(self, request, post_slug):
#        post = Blogpost.objects.get(slug=post_slug)
#
#        if not request.user == post.author:
#            return rc.FORBIDDEN # returns HTTP 401
#
#        post.delete()
#
#        return rc.DELETED # returns HTTP 204

from storage.models import Pool, Dataset

#class ArbitraryDataHandler(BaseHandler):
#    methods_allowed = ('GET',)
#
#    def read(self, request, name, data):
#        pool = Pool.objects.get(name=name)
#
#        return { 'pool': pool, 'data_length': len(data) }

class PoolHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Pool

    def read(self, request, pool_id=None):
        """
        Returns a single post if `pool_id` is given,
        otherwise a subset.
        """
        base = Pool.objects
        
        if pool_id:
            return base.get(pk=pool_id)
        else:
            return base.all() # Or base.filter(...)


class DatasetHandler(BaseHandler):
    allowed_methods = ('GET',)
    model = Dataset

    def read(self, request, dataset_id=None):
        """
        Returns a single post if `dataset_id` is given,
        otherwise a subset.
        """
        base = Dataset.objects
        
        if dataset_id:
            return base.get(pk=dataset_id)
        else:
            return base.all() # Or base.filter(...)



## LATER What about using piston to provide hooks for clustered sans so when you do a task it actually configures your entire cluster at once?
## Say a snapshot is made, run an async task to do so, that would then go through each server in the cluster and do the said action.
## Add clustered dataset could benefit greatly from this. Check status and for tasks where it applies, make it transactional (or not if wanted).
## Configure all sans from any san in the cluster in the same interface.
## The interface could be only static files, using ajax to just call these APIs.

