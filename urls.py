from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

    # default view
    url(r'^$', 'ibo.views.index', name='index'),

    # art bandit preference learning views
    url(r'^learn/$', 'ibo.views.learn', name='learn'),
    url(r'^learn/(?P<pref>\d+)/over/(?P<unpref>\d+)$', 'ibo.views.learn', name='learn_choice'),
    url(r'^clear/(?P<problem_id>\d+)$', 'ibo.views.clear', name='clear_history'),

    # session-related views (some of these are not used)
    url(r'^problem/(?P<module_name>\w+)/(?P<problem_id>\d+)/sessions$', 'ibo.views.sessions', name='sessions'),
    url(r'^problem/(?P<module_name>\w+)/(?P<problem_id>\d+)/(?P<action>\w+)-session$', 'ibo.views.sessions', name='sessions'),
    url(r'^problem/(?P<module_name>\w+)/(?P<problem_id>\d+)/(?P<action>\w+)-session/(?P<session_id>)$', 'ibo.views.sessions', name='sessions'),

    # image bandit views
    url(r'^render-raw/(?P<problem_id>\d+)/(?P<temperature>[\d\.]+)', 'ibo.views.render_raw', name='render-raw'),

    # the django admin interface
    url(r'^admin/', include(admin.site.urls)),
)
