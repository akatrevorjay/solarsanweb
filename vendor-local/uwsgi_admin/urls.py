import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.conf.urls.defaults import *

try:
    import uwsgi
    on_uwsgi = True
except:
    on_uwsgi = False

if on_uwsgi:
    urlpatterns = patterns('uwsgi_admin.views',
                            (r'^$', 'index'),
                            (r'^reload/$', 'reload')
                    )
else:
    urlpatterns = patterns('',)

