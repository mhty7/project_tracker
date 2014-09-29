from django.conf.urls import patterns, include, url

urlpatterns = patterns('ngo.apps.account.views',
    url(r'^login/$','user_login',name='login'),
    url(r'^logout/$','user_logout',name='logout'),
)
