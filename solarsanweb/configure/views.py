from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from storage.models import Pool, Dataset, Filesystem, Snapshot


class HomeListView( generic.TemplateView ):
    template_name = 'configure/home_list.html'
    def get( self, request, *args, **kwargs ):
        context = {}
        return self.render_to_response( context )


"""
Cluster
"""
from django.core.cache import cache
import gluster


class ClusterPeerListView( generic.TemplateView ):
    template_name = 'configure/cluster/peer_list.html'
    def get( self, request, *args, **kwargs ):
        peers = gluster.peer.status()
        discovered_peers = cache.get( 'RecentlyDiscoveredClusterNodes' )
        if discovered_peers:
            discovered_peers = discovered_peers['nodes']
            if '127.0.0.1' in discovered_peers:
                discovered_peers.remove( '127.0.0.1' )  # Remove localhost

        context = {
                'peers': peers['host'],
                'discovered_peers': discovered_peers,
                'peer_count': peers['peers'],
                }
        return self.render_to_response( context )


class ClusterPeerDetailView( generic.TemplateView ):
    template_name = 'configure/cluster/peer_detail.html'
    def get( self, request, *args, **kwargs ):
        peers = gluster.peer.status()

        peer_host = kwargs.get( 'peer' )
        if not peer_host in peers['host'].keys(): raise http.Http404

        peer = {peer_host: peers['host'][peer_host]}

        context = {
                'peers': peers['host'],
                'peer': peer,
                'peer_count': peers['peers'],
               }
        return self.render_to_response( context )

"""
Network
"""
from configure.models import NetworkInterface, NetworkInterfaceList, NetworkInterfaceConfig


class NetworkDetailView( generic.TemplateView ):
    template_name = 'configure/network/network_detail.html'
    def get( self, request, *args, **kwargs ):
        context = {}
        return self.render_to_response( context )


class NetworkInterfaceListView( generic.TemplateView ):
    template_name = 'configure/network/interface_list.html'
    def get( self, request, *args, **kwargs ):
        interfaces = NetworkInterfaceList()
        context = {'interfaces': interfaces, }
        return self.render_to_response( context )


class NetworkInterfaceDetailView( generic.TemplateView ):
    template_name = 'configure/network/interface_detail.html'
    def get( self, request, *args, **kwargs ):
        interface_name = kwargs['interface']
        interfaces = NetworkInterfaceList()
        context = {'interface': interface_name,
                   'interfaces': interfaces,
                   }
        return self.render_to_response( context )

from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory
#from forms import NetworkInterfaceConfigForm

#class NetworkInterfaceFormView(FormView):
#    template_name = 'configure/network/interface_form.html'
#    form_class = NetworkInterfaceConfigForm
#    success_url = reverse_lazy('network-interface-list')
#
#    def form_valid(self, form):
#        # This method is called when valid form data has been POSTed.
#        # It should return an HttpResponse.
#        #form.send_email()
#        return super(ContactView, self).form_valid(form)

class NetworkInterfaceConfigCRUDBase(object):
    model = NetworkInterfaceConfig
    slug_field = 'name'

#class NetworkInterfaceConfigCreate(NetworkInterfaceConfigCRUDBase, CreateView):
#    pass

class NetworkInterfaceConfigUpdate(NetworkInterfaceConfigCRUDBase, UpdateView):
    def get_object(self, queryset=None):
        try:
            super(NetworkInterfaceConfigUpdate, self).get_object(queryset=queryset)
        except (http.Http404):
            slug_field = self.get_slug_field()
            slug = self.kwargs.get(self.slug_url_kwarg, None)
            interface = NetworkInterface(slug)
            return interface.config

class NetworkInterfaceConfigDelete(NetworkInterfaceConfigCRUDBase, DeleteView):
    success_url = reverse_lazy('network-interface-list')


from django.views import generic

#class EmailPreferenceView(generic.FormView):
#    form_class = EmailPreferenceForm
#
#    def get(self, *args, **kwargs):
#        # You can access url variables from kwargs
#        # url: /email_preferences/geeknam > kwargs['username'] = 'geeknam'
#        # Assign to self.subscriber to be used later
#        self.subscriber = get_subscriber(kwargs['username'])
#
#    def post(self, request, *args, **kwargs):
#        # Process view when the form gets POSTed
#        pass
#
#    def get_initial(self):
#        # Populate ticks in BooleanFields
#        initial = {}
#        for s in self.subscriber.events.all():
#            initial[s.value_id] = True
#        return initial
#
#    def get_form(self, form_class):
#        # Initialize the form with initial values and the subscriber object
#        # to be used in EmailPreferenceForm for populating fields
#        return form_class(
#            initial=self.get_initial(),
#            subscriber=self.subscriber
#        )
#
#    def get_success_url(self):
#        # Redirect to previous url
#        return self.request.META.get('HTTP_REFERER', None)
#
#    def form_valid(self, form):
#        messages.info(
#            self.request,
#            "You have successfully changed your email notifications"
#        )
#        return super(EmailPreferenceView, self).form_valid(form)
#
#    def form_invalid(self, form):
#        messages.info(
#            self.request,
#            "Your submission has not been saved. Try again."
#        )
#        return super(EmailPreferenceView, self).form_invalid(form)
#
#email_preferences = EmailPreferenceView.as_view()


#def manage_authors(request):
#    AuthorFormSet = modelformset_factory(Author)
#    if request.method == "POST":
#        formset = AuthorFormSet(request.POST, request.FILES,
#                                queryset=Author.objects.filter(name__startswith='O'))
#        if formset.is_valid():
#            formset.save()
#            # Do something.
#    else:
#        formset = AuthorFormSet(queryset=Author.objects.filter(name__startswith='O'))
#    return render_to_response("manage_authors.html", {
#        "formset": formset,
#    })

#def manage_books(request, author_id):
#    author = Author.objects.get(pk=author_id)
#    BookInlineFormSet = inlineformset_factory(Author, Book)
#    if request.method == "POST":
#        formset = BookInlineFormSet(request.POST, request.FILES, instance=author)
#        if formset.is_valid():
#            formset.save()
#            # Do something. Should generally end with a redirect. For example:
#            return HttpResponseRedirect(author.get_absolute_url())
#    else:
#        formset = BookInlineFormSet(instance=author)
#    return render_to_response("manage_books.html", {
#        "formset": formset,
#    })

#class NetworkInterfaceFormView(FormView):
#    template_name = 'configure/network/interface_update.html'
#    form_class = NetworkInterfaceConfigForm
#    success_url = '/configure/network'
#
#    def form_valid(self, form):
#        # This method is called when valid form data has been POSTed.
#        # It should return an HttpResponse.
#        form.send_email()
#        return super(ContactView, self).form_valid(form)


#from myapp.forms import ContactForm
#from django.views.generic.edit import FormView
#
#class ContactView(FormView):
#    template_name = 'contact.html'
#    form_class = ContactForm
#    success_url = '/thanks/'
#
#    def form_valid(self, form):
#        # This method is called when valid form data has been POSTed.
#        # It should return an HttpResponse.
#        form.send_email()
#        return super(ContactView, self).form_valid(form)


