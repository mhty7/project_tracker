from django.conf.urls import patterns, include, url

urlpatterns = patterns('ngo.apps.board.views',
    url(r'^$','index',name='index'),
    url(r'^activity/$','activity',{},name='activity'),
    url(r'^activity/(?P<from_d>\d{8})/(?P<to_d>\d{8})/add/$','add_activity',{},name='add_activity'),
    url(r'^activity/(?P<from_d>\d{8})/(?P<to_d>\d{8})/view/$','view_activity',{},name='view_activity'),
    url(r'^activity/(?P<act_id>\d+)/edit/$','edit_activity',{},name='edit_activity'),
    url(r'^activity/(?P<act_id>\d+)/delete/$','delete_activity',{},name='delete_activity'),

    url(r'^beneficiary/$','beneficiary',{},name='beneficiary'),
    url(r'^beneficiary/(?P<ben_id>\d+)/edit/$','edit_beneficiary',{},name='edit_beneficiary'),
	url(r'^beneficiary/(?P<ben_id>\d+)/delete/$','delete_beneficiary',{},name='delete_beneficiary'),
	url(r'^beneficiary/(?P<from_d>\d{8})/(?P<to_d>\d{8})/(?P<ben_id>\d+)/view/$','view_beneficiary_history',{},name='view_beneficiary_history'),
    
)
