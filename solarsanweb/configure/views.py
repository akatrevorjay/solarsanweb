from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django import http
from django.views import generic

from storage.models import Pool, Dataset, Filesystem, Snapshot
from configure.models import ConfigEntry

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

from django_mongokit import get_database, connection
from configure.models import ClusterNode

class ClusterPeerListView( generic.TemplateView ):
    template_name = 'configure/cluster/peer_list.html'
    def get( self, request, *args, **kwargs ):
        peers = gluster.peer.status()
        #discovered_peers = cache.get( 'RecentlyDiscoveredClusterNodes' )
        col = get_database()[ClusterNode.collection_name]
        discovered_peers = list(col.find())
        if discovered_peers:
            #discovered_peers = discovered_peers['nodes']
            #if '127.0.0.1' in discovered_peers:
                #discovered_peers.remove( '127.0.0.1' )  # Remove localhost
            pass

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
#from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.core.urlresolvers import reverse_lazy
from django.forms.models import modelformset_factory
from django.contrib import messages
#from .forms import NetworkInterfaceConfigForm
import forms
from configure.models import NetworkInterface, NetworkInterfaceList, NetworkInterfaceConfig


class NetworkInterfaceListView( generic.TemplateView ):
    template_name = 'configure/network/interfaces.html'
    def get( self, request, *args, **kwargs ):
        interfaces = NetworkInterfaceList()
        context = {'interfaces': interfaces, }
        return self.render_to_response( context )


class NetworkInterfaceConfigView( generic.FormView ):
    template_name = 'configure/network/interfaces.html'
    model = NetworkInterfaceConfig
    form_class = forms.NetworkInterfaceConfigForm

    def get( self, request, *args, **kwargs ):
        self.name = kwargs['slug']
        # If we don't have the interface in question, then don't proceed.
        try:
            self.interface = NetworkInterface( self.name )
        except:
            raise http.Http404
        return super( NetworkInterfaceConfigView, self ).get( request, *args, **kwargs )

    def post( self, request, *args, **kwargs ):
        self.name = kwargs['slug']
        # If we don't have the interface in question, then don't proceed.
        try:
            self.interface = NetworkInterface( self.name )
        except:
            raise http.Http404
        return super( NetworkInterfaceConfigView, self ).post( request, *args, **kwargs )

    def get_context_data( self, **kwargs ):
        context = {}
        context.update( kwargs,
                    interface=self.name,
                    interfaces=NetworkInterfaceList(), )
        return super( NetworkInterfaceConfigView, self ).get_context_data( **context )

    def get_initial( self ):
        #initial = {}
        initial = self.interface.config.__dict__
        return initial

#    def get_form(self, form_class):
#        return form_class(
#            initial=self.get_initial(),
#        )

    def get_success_url( self ):
        # Redirect to previous url
        return self.request.META.get( 'HTTP_REFERER', None )

    def form_valid( self, form ):
        form.instance.name = self.name
        form.save()
        messages.info( 
            self.request,
            "Save successful!"
        )
        return super( NetworkInterfaceConfigView, self ).form_valid( form )

    def form_invalid( self, form ):
        messages.error( 
            self.request,
            "Something didn't seem quite right, so we didn't save. Take a gander below and see if you can spot what's up."
        )
        return super( NetworkInterfaceConfigView, self ).form_invalid( form )

network_interface_config = NetworkInterfaceConfigView.as_view()


#class NetworkDetailView( generic.TemplateView ):
#    template_name = 'configure/network/network_detail.html'
#    def get( self, request, *args, **kwargs ):
#        context = {}
#        return self.render_to_response( context )
#
#
#class NetworkInterfaceDetailView( generic.TemplateView ):
#    template_name = 'configure/network/interface_detail.html'
#    def get( self, request, *args, **kwargs ):
#        interface_name = kwargs['interface']
#        interfaces = NetworkInterfaceList()
#        context = {'interface': interface_name,
#                   'interfaces': interfaces,
#                   }
#        return self.render_to_response( context )


#class NetworkInterfaceConfigCRUDBase( object ):
#    model = NetworkInterfaceConfig
#    slug_field = 'name'
#    form_class = forms.NetworkInterfaceConfigForm
#    def form_valid( self, form ):
#        ## TODO How to set these from url kwargs properly? self.request.XXX?
#        #form.instance.name = ''
#        #form.instance.created_by = self.request.user
#        return super( NetworkInterfaceConfigCRUDBase, self ).form_valid( form )
#
#
#class NetworkInterfaceConfigUpdate( NetworkInterfaceConfigCRUDBase, generic.UpdateView ):
#    def get_object( self, queryset=None ):
#        """
#        This overrides UpdateView's get_object method for a couple reasons:
#            1. Makes it so if an interface doesn't have a configuration entry yet, it returns one with the current IP information,
#                ala new boxen or after a NIC has been added but not yet configured.
#            2. Ensures that configuration cannot be created or updated for a nonexistent interface.
#        """
#        try:
#            super( NetworkInterfaceConfigUpdate, self ).get_object( queryset=queryset )
#        except ( http.Http404 ):
#            slug_field = self.get_slug_field()
#            slug = self.kwargs.get( self.slug_url_kwarg, None )
#            try:
#                interface = NetworkInterface( slug )
#            except:
#                raise http.Http404
#            return interface.config
#
#class NetworkInterfaceConfigDelete( NetworkInterfaceConfigCRUDBase, generic.DeleteView ):
#    success_url = reverse_lazy( 'network-interface-list' )

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


## Not needed because NetworkInterfaceConfigUpdate handles creation of new objects on it's own.
#class NetworkInterfaceConfigCreate(NetworkInterfaceConfigCRUDBase, generic.CreateView):
#    pass


## Using form in standard view method
#def contact(request):
#    if request.method == 'POST': # If the form has been submitted...
#        form = ContactForm(request.POST) # A form bound to the POST data
#        if form.is_valid(): # All validation rules pass
#            # Process the data in form.cleaned_data
#            # ...
#            return HttpResponseRedirect('/thanks/') # Redirect after POST
#    else:
#        form = ContactForm() # An unbound form
#
#    return render(request, 'contact.html', {
#        'form': form,
#    })


#class ProcessAddQuote(BaseCreateView, JSONResponseMixin):
#    """
#    View mixin used built-in view class BaseCreateView 
#    `https://docs.djangoproject.com/en/dev/ref/class-based-views/#django.views.generic.edit.BaseCreateView`
#    And proposed json serialize mixin to serialize response, i.o we using AJAX 
#    in form displaying and processing.
#    
#    BaseCreateView are creates view form form data, every time new instance. 
#    This class using ModeFormMixin 
#    `https://docs.djangoproject.com/en/dev/ref/class-based-views/#django.views.generic.edit.ModelFormMixin`
#    `https://docs.djangoproject.com/en/dev/ref/class-based-views/#django.views.generic.edit.ProcessFormView`
#    which construct modelform view as usual and ProcessFormView which validate and process form.
#    """   
#    form_class = QuoteAdd
#    
#    def form_invalid(self, form):
#        """
#        Collect errors for serializing.
#        """
#        errors = {'errors':{}}
#        for i in form.errors.keys():
#            errors['errors'][i] = form.errors[i].as_text()
#        return self.render_json_to_response(errors)
#    
#    def convert_context_to_json(self, context):
#        """
#        Method are serialze saved quote instance or form errors.
#        We need to serialize errors too, to show user how to fill the form.
#        """
#        print type(context)
#        try:
#            isinstance(context.__class__(), DictionaryType)
#        except TypeError:
#            raise TypeError('context object is not serializeble')
#        else:
#            isinstance(context.__class__(), models.Model)            
#            context = {'author': context.author, 'content': context.content}
#        finally:
#            return super(ProcessAddQuote, self).convert_context_to_json(context)
#    
#    def form_valid(self, form):
#        """
#        If form is valid user field appoint to current user. Then save instance.
#        Saved instance set to regrialize.
#        """
#        self.object = form.save(commit=False)
#        self.object.user = self.request.user
#        self.object.save()
#        quote_obj = Quote.objects.get(id=self.object.id)
#        return self.render_json_to_response(quote_obj)



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


