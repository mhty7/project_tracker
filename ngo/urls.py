from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

admin.site.site_header = 'Administration'

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'ngo.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'',include('ngo.apps.board.urls')),
    url(r'^user/',include('ngo.apps.account.urls')),
)
