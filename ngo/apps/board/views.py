from django.shortcuts import render
from ngo import conf
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.core.urlresolvers import reverse
from ngo.apps.board.forms import ActivityDateForm,BeneficiaryForm,ActivityForm, \
	RequiredFormSet,RequiredModelFormSet,BeneficiaryTypeForm,BeneficiaryAttendanceForm, \
	GroupForm,BeneficiaryRegisterForm,MyModelFormsetBase,ActivityTypeForm,StatisticsForm
from django.http import HttpResponseRedirect, HttpResponse,HttpResponseBadRequest
from django.contrib import messages
from datetime import date
from datetime import datetime
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet,modelformset_factory
from django.http import Http404
from django.db.models import Q
from ngo.apps.board.models import *
from django.contrib.auth.models import User
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
import math
import json
from django.utils.functional import curry
from dateutil import rrule
from dateutil.relativedelta import relativedelta
from django import forms
from django.template.loader import render_to_string

@login_required
def index(request):
	return render(request,'board/index.html',{'conf':conf,'title':'home'})


@login_required
def view_beneficiary_history(request,from_d,to_d,ben_id,template='board/view_beneficiary_history.html'):
	try:
		f_d=datetime.strptime(from_d,'%m%d%Y')
		t_d=datetime.strptime(to_d,'%m%d%Y')
	except ValueError:
		return HttpResponse(status=400)

	if (t_d-f_d).days<0:
		return HttpResponse(status=400)


	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			bens=Beneficiary.objects.get(id=ben_id)
		else:
			bens=auser.beneficiaries.get(id=ben_id)
	except ObjectDoesNotExist:
		raise Http404

	

	bens_contents={'ty':dict(Beneficiary.B_TYPE)[bens.ty],
		'fname':bens.fname,
		'lname':bens.lname,
		'group':bens.group.all()
	}

	ty=None
	aform=ActivityTypeForm()
	if request.method=='POST' and 'choice' in request.POST:
		aform=ActivityTypeForm(request.POST)
		if aform.is_valid():
			ty=aform.cleaned_data['choice']
	elif request.method=='GET' and 'ty' in request.GET:
		ty=request.GET.get('ty',None)
		aform.fields['choice'].initial=ty


	fset=modelformset_factory(Activity,formset=MyModelFormsetBase,form=BeneficiaryAttendanceForm,extra=0)
	fset.form = staticmethod(curry(BeneficiaryAttendanceForm,extra_args=MyModelFormsetBase.extra_args))

	contents=[]


	q=bens.user.activities.filter(fdate__gte=f_d,fdate__lte=t_d).order_by('fdate')
	if ty:
		q=q.filter(activity_ty=ty)

	paginator=Paginator(q,10)
	page=request.GET.get('page')
	try:
		contents=paginator.page(page)
	except PageNotAnInteger:
		contents=paginator.page(1)
	except EmptyPage:
		contents=paginator.page(paginator.num_pages)

	adjacent_pages=3
	startPage = max(contents.number - adjacent_pages, 1)
	endPage = contents.number + adjacent_pages
	if endPage >= contents.paginator.num_pages : 
		endPage = contents.paginator.num_pages
	page_numbers = [n for n in range(startPage, endPage+1) if n > 0 and n <= contents.paginator.num_pages]



	page_query = q.filter(id__in=[c.id for c in contents])



	if request.method=='POST':
		if 'save' in request.POST:
			forms=fset(request.POST,queryset=page_query,extra_args=bens)
			if forms.is_valid():
				for f in forms:
					f.save()
				messages.add_message(request,messages.SUCCESS,'The data have been successfully edited.')
				return HttpResponseRedirect(reverse('view_beneficiary_history',
							kwargs={'from_d':from_d,
								'to_d':to_d,
								'ben_id':bens.id}))
		else:
			forms=fset(queryset=page_query,extra_args=bens)

	else :
		forms=fset(queryset=page_query,extra_args=bens)


	renders={}
	renders['aform']=aform
	renders['bform']=[]
	json_data={}
	for f in forms:
		renders['bform'].append({'center':f.activity.user.username,'activity_ty':dict(Activity.A_TYPE)[f.activity.activity_ty],
			'fdate':f.activity.fdate,'tdate':f.activity.tdate,'form':f})
		dic={}
		for aw in f.activity.description.all():
			dic[aw.week]=aw.description
		json_data[f.activity.id]=dic
	json_data=json.dumps(json_data)

	return render(request,template,{'conf':conf,'page_numbers':page_numbers,'bens_contents':bens_contents,'contents':contents,'renders':renders,
		'ty':ty,'from_d':from_d,'to_d':to_d,'ben_id':ben_id,'forms':forms,'json_data':json_data,'title':'view activity',})



@login_required
@transaction.atomic
def edit_beneficiary(request,ben_id,template='board/edit_beneficiary.html'):

	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			bens=Beneficiary.objects.get(id=ben_id)
		else:
			bens=auser.beneficiaries.get(id=ben_id)
	except ObjectDoesNotExist:
		raise Http404

	editing_user=bens.user
	
	post_kwargs={'user':editing_user}
	if request.method== 'POST':
		if 'save' in request.POST:
			bform=BeneficiaryRegisterForm(request.POST,instance=bens,**post_kwargs)
			if bform.is_valid():
				bform.save()
				messages.add_message(request,messages.SUCCESS,'The data have been successfully edited.')
				return HttpResponseRedirect(reverse('edit_beneficiary',kwargs={'ben_id':ben_id}))
			else:
				messages.add_message(request,messages.WARNING,'The process went wrong.')
				return HttpResponseRedirect(reverse('edit_beneficiary',kwargs={'ben_id':ben_id}))


		else:
			dform=ActivityDateForm(request.POST,extra=None,)
			bform=BeneficiaryRegisterForm(instance=bens,**post_kwargs)
		
		if dform.is_valid():
			if request.POST.get('search'):
				#if (dform.cleaned_data['to_date']-dform.cleaned_data['from_date']).days<0:
				#	messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
				#	return HttpResponseRedirect(reverse('edit_beneficiary',kwargs={'ben_id':ben_id}))
				#else :
				return HttpResponseRedirect(reverse('view_beneficiary_history',
					kwargs={'from_d':dform.cleaned_data['from_date'].strftime('%m%d%Y'),
						'to_d':dform.cleaned_data['to_date'].strftime('%m%d%Y'),
						'ben_id':bens.id}))
		else:
			messages.add_message(request,messages.WARNING,"<br />".join(dform.non_field_errors()))
				
	else:
		dform=ActivityDateForm(extra=None)
		bform=BeneficiaryRegisterForm(instance=bens,**post_kwargs)

	return render(request,template,{'conf':conf,'dform':dform,'bform':bform,'title':'edit beneficiary','ben_id':ben_id,})



@login_required
@transaction.atomic
def delete_beneficiary(request,ben_id,template=''):
	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			bens=Beneficiary.objects.get(id=ben_id)
		else:
			bens=auser.beneficiaries.get(id=ben_id)
	except ObjectDoesNotExist:
		raise Http404
	bens.delete()
	messages.add_message(request,messages.SUCCESS,'The data have been successfully deleted.')
	return HttpResponseRedirect(reverse('beneficiary',))

@login_required
@transaction.atomic
def beneficiary(request,template='board/beneficiary.html'):
	try:
		auser=User.objects.get(id=request.user.id)
	except ObjectDoesNotExist:
		raise Http404

	if auser.is_superuser:
		bens=Beneficiary.objects.all().order_by('user','id')
	else:
		bens=auser.beneficiaries.all().order_by('user','id')
	
	post_kwargs={'user':request.user}
	capsule=[]
	if request.method=='POST':
		if 'add' in request.POST:
			bform=BeneficiaryRegisterForm(request.POST,**post_kwargs)
			if bform.is_valid():
				b=bform.save()
				b.save()
				messages.add_message(request,messages.SUCCESS,'The data have been successfully added.')
				return HttpResponseRedirect(reverse('beneficiary'))
	else:
		bform=BeneficiaryRegisterForm(**post_kwargs)
		
	for ben in bens:
		center=ben.user.username
		a=ben.lname
		b=ben.fname
		ty=dict(Beneficiary.B_TYPE)[ben.ty]
		group=ben.group.all().order_by('id')
		capsule.append({'center':center,'id':ben.id,'a':a,'b':b,'ty':ty,'group':group})

	paginator=Paginator(capsule,10)
	page=request.GET.get('page')
	try:
		contents=paginator.page(page)
	except PageNotAnInteger:
		contents=paginator.page(1)
	except EmptyPage:
		contents=paginator.page(paginator.num_pages)
	
	adjacent_pages=3
	startPage = max(contents.number - adjacent_pages, 1)
	endPage = contents.number + adjacent_pages
	if endPage >= contents.paginator.num_pages : 
		endPage = contents.paginator.num_pages
	page_numbers = [n for n in range(startPage, endPage+1) if n > 0 and n <= contents.paginator.num_pages]



	return render(request,template,{'conf':conf,'title':'beneficiary','bform':bform,'contents':contents,'page_numbers':page_numbers})


@login_required
@transaction.atomic
def delete_activity(request,act_id,template=''):
	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			act=Activity.objects.get(id=act_id)
		else:
			act=auser.activities.get(id=act_id)
	except ObjectDoesNotExist:
		raise Http404
	act.delete()
	messages.add_message(request,messages.SUCCESS,'The data have been successfully deleted.')
	return HttpResponseRedirect(reverse('activity',))

@login_required
@transaction.atomic
def edit_activity(request,act_id,template='board/add_activity.html'):
	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			act=Activity.objects.get(id=act_id)
		else:
			act=auser.activities.get(id=act_id)
	except ObjectDoesNotExist:
		raise Http404
	
	editing_user=act.user
	aw=act.description.all()
	bens=Beneficiary.objects.filter(activityWeek__in=aw).distinct()
	f_d=act.fdate
	t_d=act.tdate
	if bens.count()==0:
		e=1
	else:
		e=0

	bffset=modelformset_factory(Beneficiary,extra=e,form=BeneficiaryForm,formset=RequiredModelFormSet,max_num=50)
	bffset.form = staticmethod(curry(BeneficiaryForm,extra_args=RequiredModelFormSet.extra_args))
	try:
		auser=User.objects.get(id=editing_user.id)
	except ObjectDoesNotExist:
		raise Http404
	data={}
	post_kwargs={'user':editing_user}
	data['beneficiaries']={}
	for b in auser.beneficiaries.all().order_by('id'):
		weeks=[int(i) for i in b.activityWeek.all().values_list('week',flat=True)]
		dic={'id':b.id,'lname':b.lname,'fname':b.fname,'ty':b.ty,'weeks':weeks}
		data['beneficiaries'][b.id]=dic

	data['groups']=[]
	for a in auser.beneficiaryGroup.order_by('id'):
		data['groups'].append({'id':a.id,'name':a.name})
	data=json.dumps(data)
	if request.method== 'POST':
		aform=ActivityForm(request.POST,instance=act,**post_kwargs)
		bform=bffset(request.POST,queryset=bens,extra_args=act)
		dform=ActivityDateForm(request.POST,extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})
		dform.fields['to_date'].widget=forms.HiddenInput()
		if dform.is_valid():
			if request.POST.get('save'):
				#if (dform.cleaned_data['to_date']-dform.cleaned_data['from_date']).days<0:
				#	messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
				#	return HttpResponseRedirect(reverse('edit_activity',kwargs={'act_id':act_id}))
				if bform.is_valid():
					if aform.is_valid():
						frd=dform.cleaned_data['from_date']
						tod=frd+relativedelta(months=1)
						a=aform.save(fd=frd,td=tod)
						#a.beneficiaries.clear()
						for aw in a.description.all():
							aw.beneficiaries.clear()
						for form in bform.forms:
							b=form.save(act=a,user=editing_user)
						messages.add_message(request,messages.SUCCESS,'The data have been successfully edited.')
						return HttpResponseRedirect(reverse('edit_activity',kwargs={'act_id':act_id}))
				else :
					messages.add_message(request,messages.WARNING,"<br />".join(bform.non_form_errors()))

	else:
		aform=ActivityForm(instance=act,**post_kwargs)
		bform=bffset(queryset=bens,extra_args=act)
		dform=ActivityDateForm(extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})
		dform.fields['to_date'].widget=forms.HiddenInput()

	return render(request,template,{'conf':conf,'dform':dform,'aform':aform,'bform':bform,'title':'edit activity'
		,'act_id':act_id,'data':data,})




@login_required
def view_activity(request,from_d,to_d,template='board/view_activity.html'):
	try:
		f_d=datetime.strptime(from_d,'%m%d%Y')
		t_d=datetime.strptime(to_d,'%m%d%Y')
	except ValueError:
		return HttpResponse(status=400)

	if (t_d-f_d).days<0:
		return HttpResponse(status=400)

	try:
		auser=User.objects.get(id=request.user.id)
	except ObjectDoesNotExist:
		raise Http404

	if auser.is_superuser:
		acts=Activity.objects.all().order_by('user')
	else:
		acts=auser.activities.all().order_by('user')
	

	
	capsule=dict()

	ty=None
	aform=ActivityTypeForm()
	if request.method=='POST' and 'choice' in request.POST:
		aform=ActivityTypeForm(request.POST)
		if aform.is_valid():
			ty=aform.cleaned_data['choice']
	elif request.method=='GET' and 'ty' in request.GET:
		ty=request.GET.get('ty',None)
		aform.fields['choice'].initial=ty


	for dt in rrule.rrule(rrule.MONTHLY,dtstart=f_d, until=t_d):
		tod=dt+relativedelta(months=1)
		d=capsule.setdefault(dt,{})
		d['tod']=[dt.strftime('%m%d%Y'),tod.strftime('%m%d%Y')]
		d['acts']=[]
		tmp=acts.filter(fdate__gte=dt,fdate__lt=tod)
		if ty:
			tmp=tmp.filter(activity_ty=ty)
		for ac in tmp:
			center=ac.user.username
			a=dict(Activity.A_TYPE)[ac.activity_ty]
			obj={}
			for i in WEEK_CHOICES:
				t=ac.description.get(week=i[0])
				for ii in Beneficiary.B_TYPE:
					obj[i[0]+ii[0]]=t.beneficiaries.filter(ty=ii[0]).count()
			d['acts'].append({'center':center,'id':ac.id,'a':a,'obj':obj})



	capsule=sorted(capsule.items())

	#form=ActivityDateForm(extra={'from_date':(f_d.month,f_d.year,f_d.day),'to_date':(t_d.month,t_d.year,t_d.day),'editable':False,},)

	ty=None
	aform=ActivityTypeForm()
	if request.method=='POST' and 'choice' in request.POST:
		aform=ActivityTypeForm(request.POST)
		if aform.is_valid():
			ty=aform.cleaned_data['choice']
	elif request.method=='GET' and 'ty' in request.GET:
		ty=request.GET.get('ty',None)
		aform.fields['choice'].initial=ty



	renders={'from_date':f_d,'to_date':t_d,'aform':aform}

	paginator=Paginator(capsule,3)
	page=request.GET.get('page')
	try:
		contents=paginator.page(page)
	except PageNotAnInteger:
		contents=paginator.page(1)
	except EmptyPage:
		contents=paginator.page(paginator.num_pages)

	adjacent_pages=3
	startPage = max(contents.number - adjacent_pages, 1)
	endPage = contents.number + adjacent_pages
	if endPage >= contents.paginator.num_pages : 
		endPage = contents.paginator.num_pages
	page_numbers = [n for n in range(startPage, endPage+1) if n > 0 and n <= contents.paginator.num_pages]


	json_data={}
	for c in contents:
		if c[1]["acts"]:
			for cc in c[1]["acts"]:
				dic={}
				aws=ActivityWeeklyDescription.objects.filter(activity__id=cc['id']).prefetch_related('beneficiaries')
				for aw in aws:
					w=aw.week
					dic[w]={}
					d=aw.description
					dic[w]['d']=d
					dicc=dict()
					for a in aw.beneficiaries.all().values_list('ty','lname','fname',):
						diccc=dicc.setdefault(a[0],[])
						diccc.append(a[1]+' '+a[2])
						dicc[a[0]]=diccc
					dic[w]['b']=dicc
				json_data[u'%s'%cc['id']]=dic
	json_data=json.dumps(json_data)
					

	return render(request,template,{'conf':conf,'page_numbers':page_numbers,'renders':renders,'contents':contents,
		'ty':ty,'from_d':from_d,'to_d':to_d,'json_data':json_data,'title':'view activity',})







@login_required
@transaction.atomic
def add_activity(request,from_d,to_d,template='board/add_activity.html'):
	try:
		f_d=datetime.strptime(from_d,'%m%d%Y')
		t_d=datetime.strptime(to_d,'%m%d%Y')
	except ValueError:
		return HttpResponse(status=400)

	if (t_d-f_d).days<0:
		return HttpResponse(status=400)

	try:
		auser=User.objects.get(id=request.user.id)
	except ObjectDoesNotExist:
		raise Http404
	data={}
	post_kwargs={'user':request.user}
	data['beneficiaries']={}
	for b in auser.beneficiaries.all().order_by('id'):
		#weeks=[int(i) for i in b.activityWeek.all().values_list('week',flat=True)]
		dic={'id':b.id,'lname':b.lname,'fname':b.fname,'ty':b.ty,}
		data['beneficiaries'][b.id]=dic
	data['groups']=[]
	for a in auser.beneficiaryGroup.order_by('id'):
		data['groups'].append({'id':a.id,'name':a.name});

	data=json.dumps(data)
	bffset=formset_factory(BeneficiaryForm,max_num=50,formset=RequiredFormSet)
	if request.method== 'POST':
		aform=ActivityForm(request.POST,**post_kwargs)
		bform=bffset(request.POST)
		dform=ActivityDateForm(request.POST,extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})
		dform.fields['to_date'].widget=forms.HiddenInput()

		if dform.is_valid():

			if request.POST.get('save'):
				#if (dform.cleaned_data['to_date']-dform.cleaned_data['from_date']).days<0:
				#	messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
				#	return HttpResponseRedirect(reverse('add_activity',kwargs={'from_d':from_d,'to_d':to_d}))
				if bform.is_valid():
					if aform.is_valid():
						frd=dform.cleaned_data['from_date']
						tod=frd+relativedelta(months=1)
						a=aform.save(fd=frd,td=tod)
						for form in bform.forms:
							b=form.save(act=a,user=request.user)
						messages.add_message(request,messages.SUCCESS,'The data have been successfully added.')
						return HttpResponseRedirect(reverse('activity'))
				else:
					messages.add_message(request,messages.WARNING,"<br />".join(bform.non_form_errors()))

				
	else:
		aform=ActivityForm(**post_kwargs)
		bform=bffset()
		dform=ActivityDateForm(extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})
		dform.fields['to_date'].widget=forms.HiddenInput()

	return render(request,template,{'conf':conf,'dform':dform,'aform':aform,'bform':bform,'title':'add activity'
		,'from_d':from_d,'to_d':to_d,'data':data,})




@login_required
def activity(request,template='board/activity.html'):
	if request.method == 'POST':
		add_form = ActivityDateForm(request.POST,extra=None)
		if add_form.is_valid():
			if request.POST.get('add'):
				#if (add_form.cleaned_data['to_date']-add_form.cleaned_data['from_date']).days<0:
				#	messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
				#	return HttpResponseRedirect(reverse('activity'))
				#else :
				return HttpResponseRedirect(reverse('view_activity',kwargs={'from_d':add_form.cleaned_data['from_date'].strftime('%m%d%Y'),
						'to_d':add_form.cleaned_data['to_date'].strftime('%m%d%Y')}))
		else:
			messages.add_message(request,messages.WARNING,"<br />".join(add_form.non_field_errors()))
	else :
		add_form = ActivityDateForm(extra=None)
	return render(request,template,{'conf':conf,'add_form':add_form,'title':'activity'})



@login_required
@transaction.atomic
def mygroup(request,template='board/mygroup.html'):
	try:
		auser=User.objects.get(id=request.user.id)
	except ObjectDoesNotExist:
		raise Http404

	if auser.is_superuser:
		groups=BeneficiaryGroup.objects.all().order_by('user','id')
	else:
		groups=auser.beneficiaryGroup.all().order_by('user','id')


	capsule=[]
	post_kwargs={'user':request.user}
	if request.method=='POST':
		gform=GroupForm(request.POST,**post_kwargs)

		if gform.is_valid():
			gform.save()
			messages.add_message(request,messages.SUCCESS,'The data have been successfully added.')
			return HttpResponseRedirect(reverse('mygroup'))


	else:
		gform=GroupForm(**post_kwargs)
		
	for group in groups:
		center=group.user
		a=group.name
		b=group.beneficiaries.all().order_by('id')
		capsule.append({'center':center.username,'cid':center.id,'id':group.id,'a':a,'b':b,})

	paginator=Paginator(capsule,10)
	page=request.GET.get('page')
	try:
		contents=paginator.page(page)
	except PageNotAnInteger:
		contents=paginator.page(1)
	except EmptyPage:
		contents=paginator.page(paginator.num_pages)
	adjacent_pages=3
	startPage = max(contents.number - adjacent_pages, 1)
	endPage = contents.number + adjacent_pages
	if endPage >= contents.paginator.num_pages : 
		endPage = contents.paginator.num_pages
	page_numbers = [n for n in range(startPage, endPage+1) if n > 0 and n <= contents.paginator.num_pages]
	return render(request,template,{'conf':conf,'page_numbers':page_numbers,'contents':contents,'title':'mygroup','gform':gform,})



@login_required
@transaction.atomic
def statistics(request,template='board/statistics.html'):
	try:
		auser=User.objects.get(id=request.user.id)
	except ObjectDoesNotExist:
		raise Http404

	if auser.is_superuser:
		pass
		#groups=BeneficiaryGroup.objects.all().order_by('user','id')
	else:
		pass
		#groups=auser.beneficiaryGroup.all().order_by('user','id')


	"""
	chronological order check in form validations.
	"""

	if request.POST:
		form=StatisticsForm(request.POST)
		if form.is_valid():
			if request.is_ajax():
				achoice=form.cleaned_data["achoice"]
				bchoice=form.cleaned_data["bchoice"]
				from_date=form.cleaned_data["from_date"]
				f_week=form.cleaned_data["f_week"]
				to_date=form.cleaned_data["to_date"]
				t_week=form.cleaned_data["t_week"]
				center=form.cleaned_data["center"]
				distinct=form.cleaned_data["distinct"]

				try:
					auser=User.objects.get(id=center)
				except ObjectDoesNotExist:
					raise Http404
				bens=auser.beneficiaries.all().select_related()
				
				queryQ=Q()

				frd=from_date+relativedelta(months=1)
				tod=to_date-relativedelta(months=1)
				queryQ.add(Q(activityWeek__activity__fdate__gte=frd) & Q(activityWeek__activity__fdate__lte=tod),Q.AND)
				fwarr=WEEK_CHOICES[int(f_week)-1:]
				twarr=WEEK_CHOICES[:int(t_week)]

				if(from_date==to_date):
					fwarr=WEEK_CHOICES[int(f_week)-1:int(t_week)]
					twarr=WEEK_CHOICES[int(f_week)-1:int(t_week)]

				queryQ.add(Q(activityWeek__activity__fdate=from_date) & Q(activityWeek__week__in=[w[0] for w in fwarr]),Q.OR)
				queryQ.add(Q(activityWeek__activity__fdate=to_date) & Q(activityWeek__week__in=[h[0] for h in twarr]),Q.OR)

				if(achoice!="0"):
					queryQ.add(Q(activityWeek__activity__activity_ty=achoice),Q.AND)

				if(bchoice!="0"):
					queryQ.add(Q(ty=bchoice),Q.AND)

				if distinct:
					num=bens.filter(queryQ).all().distinct().count()
				else :
					num=bens.filter(queryQ).all().count()

				data={}
				data["timestamp"]=datetime.now().strftime('%H:%M:%S %b.%d %Y')
				data["number"]=num
				data["distinct"]=distinct
				data["from"]=from_date.strftime('%b.%d %Y ')+dict(WEEK_CHOICES)[f_week]+' week'
				data["to"]=to_date.strftime('%b.%d %Y ')+dict(WEEK_CHOICES)[t_week]+' week'
				data["center"]=auser.username
				data["achoice"]=dict(StatisticsForm.ACHOICE)[achoice]
				data["bchoice"]=dict(StatisticsForm.BCHOICE)[bchoice]

				data["contents"] = render_to_string('forms/statistics.html',data)


				return HttpResponse(json.dumps(data))
		else:
			if request.is_ajax():
				errors={}
				if form.errors:
					for error in form.errors:
						e=form.errors[error]
						errors[error]=e
				errors["non_field_errors"]="<br />".join(form.non_field_errors())
				return HttpResponseBadRequest(json.dumps(errors))


	else:
		form = StatisticsForm()


	return render(request,template,{'conf':conf,'form':form,'title':'statistics',})






@login_required
@transaction.atomic
def delete_group(request,grp_id,template=''):
	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			grp=BeneficiaryGroup.objects.get(id=grp_id)
		else:
			grp=auser.beneficiaryGroup.get(id=grp_id)
	except ObjectDoesNotExist:
		raise Http404
	grp.delete()
	messages.add_message(request,messages.SUCCESS,'The data have been successfully deleted.')
	return HttpResponseRedirect(reverse('mygroup',))

@login_required
def group_list_ajax(request):
	gid=request.POST.get('gid')
	cid=request.POST.get('cid')

	try:
		auser=User.objects.get(id=request.user.id)
		euser=User.objects.get(id=cid)
		if auser.is_superuser:
			bg=BeneficiaryGroup.objects.get(id=gid,user=euser)

		else:
			bg=auser.beneficiaryGroup.get(id=gid,user=euser)
	except ObjectDoesNotExist:
		raise Http404

	nodes = bg.beneficiaries.order_by('id')
	data = {}
	data['beneficiaries'] = []
	for n in nodes:
		data['beneficiaries'].append({'id':n.id,'lname':n.lname,'fname':n.fname,'ty':n.ty,})
	return HttpResponse(json.dumps(data))



@login_required
def beneficiary_list_ajax(request):
	gid=request.POST.get('gid')
	cid=request.POST.get('cid')
	try:
		auser=User.objects.get(id=request.user.id)
		euser=User.objects.get(id=cid)
		if auser.is_superuser:
			grp=BeneficiaryGroup.objects.get(id=gid,user=euser)

		else:
			grp=auser.beneficiaryGroup.get(id=gid,user=euser)
	except ObjectDoesNotExist:
		raise Http404

	nodes = euser.beneficiaries.exclude(id__in=grp.beneficiaries.all()).order_by('id')
	data = {}
	data['beneficiaries'] = []
	for n in nodes:
		data['beneficiaries'].append({'id':n.id,'lname':n.lname,'fname':n.fname,'ty':n.ty,})
	return HttpResponse(json.dumps(data))



@login_required
def beneficiary_add_ajax(request):
	gid=request.POST.get('gid')
	bid=request.POST.get('bid')
	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			grp=BeneficiaryGroup.objects.get(id=gid)
			ben=Beneficiary.objects.get(id=bid)
		else:
			grp=auser.beneficiaryGroup.get(id=gid)
			ben=auser.beneficiaries.get(id=bid)
	except ObjectDoesNotExist:
		raise Http404
	grp.beneficiaries.add(ben)
	data = {}
	url=reverse('edit_beneficiary',kwargs={'ben_id':ben.id})
	data['beneficiaries']={'id':ben.id,'lname':ben.lname,'fname':ben.fname,'ty':ben.ty,'url':url}
	return HttpResponse(json.dumps(data))

@login_required
def beneficiary_remove_ajax(request):
	gid=request.POST.get('gid')
	bid=request.POST.get('bid')
	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			grp=BeneficiaryGroup.objects.get(id=gid)
			ben=Beneficiary.objects.get(id=bid)
		else:
			grp=auser.beneficiaryGroup.get(id=gid)
			ben=auser.beneficiaries.get(id=bid)
	except ObjectDoesNotExist:
		raise Http404
	grp.beneficiaries.remove(ben)
	data = {}
	data['beneficiaries']={'id':ben.id,'lname':ben.lname,'fname':ben.fname,'ty':ben.ty,}
	return HttpResponse(json.dumps(data))


