from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'ibo.views.index', name='index'),
    url(r'^learn/$', 'ibo.views.learn', name='learn'),
    url(r'^learn/(?P<pref>\d+)/over/(?P<unpref>\d+)$', 'ibo.views.learn', name='learn_choice'),

    url(r'^clear/(?P<problem_id>\d+)$', 'ibo.views.clear', name='clear_history'),
    url(r'^problem/(?P<problem_id>\d+)/sessions$', 'ibo.views.sessions', name='sessions'),
    url(r'^problem/(?P<problem_id>\d+)/(?P<action>\w+)-session$', 'ibo.views.sessions', name='sessions'),
    url(r'^problem/(?P<problem_id>\d+)/(?P<action>\w+)-session/(?P<session_id>)$', 'ibo.views.sessions', name='sessions'),

    url(r'^admin/', include(admin.site.urls)),
)
