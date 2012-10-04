#!/usr/bin/env python

"""
This is an expanded version of "Resolve URLs to view name" without the monkey-patching.

Simply pass in a URL such as '/events/rsvp/some_conference/' and you'll get back the view name or function (if name isn't available) and the arguments to it, eg 'events_rsvp', [], {'event_slug':'some_conference'}.

Example (blatantly copied from previous snippet):

=== urlconf ====
urlpatterns = patterns(''
    (r'/some/url', 'app.views.view'),
    url(r'/some/other/(?P<url>\w+)', 'app.views.other.view', name='this_is_a_named_view'),
    url(r'/yet/another/(?P<url>\w+)/(\d+)', 'app.views.yetanother.view', name='one_with_args'),
)

=== example usage in interpreter ===
>>> from some.where import resolve_to_name
>>> print resolve_to_name('/some/url')
('app.views.view',[],{})
>>> print resolve_to_name('/some/other/url')
('this_is_a_named_view',[],{'url':'url'})
>>> print resolve_to_name('/yet/another/url/5')
('one_with_args',[5],{'url':'url'})
"""

from django.core.urlresolvers import RegexURLResolver, RegexURLPattern, Resolver404, get_resolver

__all__ = ('resolve_to_name',)

def _parse_match(match):
    args = list(match.groups())
    kwargs = match.groupdict()
    for val in kwargs.values():
        args.remove(val)
    return args, kwargs

def _pattern_resolve_to_name(self, path):
    match = self.regex.search(path)
    if match:
        name = ""
        if self.name:
            name = self.name
        elif hasattr(self, '_callback_str'):
            name = self._callback_str
        else:
            name = "%s.%s" % (self.callback.__module__, self.callback.func_name)
        args, kwargs = _parse_match(match)
        return name, args, kwargs

def _resolver_resolve_to_name(self, path):
    tried = []
    match = self.regex.search(path)
    if match:
        new_path = path[match.end():]
        for pattern in self.url_patterns:
            try:
                if isinstance(pattern,RegexURLPattern):
                    nak =  _pattern_resolve_to_name(pattern,new_path)
                else:
                    nak = _resolver_resolve_to_name(pattern,new_path)
            except Resolver404, e:
                tried.extend([(pattern.regex.pattern + '   ' + t) for t in e.args[0]['tried']])
            else:
                if nak:
                    return nak # name, args, kwargs
                tried.append(pattern.regex.pattern)
        raise Resolver404, {'tried': tried, 'path': new_path}


def resolve_to_name(path, urlconf=None):
    r = get_resolver(urlconf)
    if isinstance(r,RegexURLPattern):
        return _pattern_resolve_to_name(r,path)
    else:
        return _resolver_resolve_to_name(r,path)


