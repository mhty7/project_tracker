from django.shortcuts import render
from ngo import conf
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from ngo.apps.board.forms import ActivityDateForm,BeneficiaryForm,ActivityForm,RequiredFormSet,RequiredModelFormSet,BeneficiaryTypeForm,BeneficiaryAttendanceForm
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from datetime import date
from datetime import datetime
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet,modelformset_factory
from django.http import Http404
from django.db.models import Q
from ngo.apps.board.models import Beneficiary,Activity
from django.contrib.auth.models import User
from django.core.paginator import Paginator,EmptyPage, PageNotAnInteger
from django.core.exceptions import ObjectDoesNotExist
import math
import json

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
	}
	
	fset=formset_factory(BeneficiaryAttendanceForm,extra=0)

	contents=[]
	fset_init=[]
	
	for ac in bens.user.activities.filter(fdate__gte=f_d,tdate__lte=t_d):
		center=ac.user.username
		a=dict(Activity.A_TYPE)[ac.activity_ty]
		b=ac.description
		c={
			'from_date':(ac.fdate.month,ac.fdate.year,math.ceil(ac.fdate.day/7)),
			'to_date':(ac.tdate.month,ac.tdate.year,math.ceil(ac.tdate.day/7)),}
		fset_init.append({'choice':ac.beneficiaries.filter(id=bens.id).exists(),'id':ac.id})
		contents.append({'center':center,'a':a,'b':b,'c':c,})
	
	if request.method=='POST':
		forms=fset(request.POST,initial=fset_init)
		if forms.is_valid():
			d=dict((d['id'],d['choice']) for d in fset_init)
			for f in forms:
				if str(f.cleaned_data['choice']) != str(d.get(f.cleaned_data['id'])):
					try:
						a=Activity.objects.get(id=f.cleaned_data['id'])
					except:
						continue
					if f.cleaned_data['choice']=='True':
						bens.activity.add(a)
					else:
						bens.activity.remove(a)
			messages.add_message(request,messages.SUCCESS,'The data have been successfully edited.')
			return HttpResponseRedirect(reverse('view_beneficiary_history',
						kwargs={'from_d':from_d,
							'to_d':to_d,
							'ben_id':bens.id}))

	else:
		forms=fset(initial=fset_init)

	for i in range(len(forms)):
		contents[i]['d']=forms[i]


	return render(request,template,{'conf':conf,'contents':contents,'bens_contents':bens_contents,
		'from_d':from_d,'to_d':to_d,'ben_id':ben_id,'forms':forms,'title':'view activity',})



@login_required
def edit_beneficiary(request,ben_id,template='board/edit_beneficiary.html'):

	try:
		auser=User.objects.get(id=request.user.id)
		if auser.is_superuser:
			bens=Beneficiary.objects.get(id=ben_id)
		else:
			bens=auser.beneficiaries.get(id=ben_id)
	except ObjectDoesNotExist:
		raise Http404
	

	if request.method== 'POST':
		if 'save' in request.POST:
			bform=BeneficiaryForm(request.POST,instance=bens,)
			if bform.is_valid():
				bform.save()
				messages.add_message(request,messages.SUCCESS,'The data have been successfully edited.')
				return HttpResponseRedirect(reverse('edit_beneficiary',kwargs={'ben_id':ben_id}))
			else:
				messages.add_message(request,messages.WARNING,'The process went wrong.')
				return HttpResponseRedirect(reverse('edit_beneficiary',kwargs={'ben_id':ben_id}))


		else:
			dform=ActivityDateForm(request.POST,extra=None,)
			bform=BeneficiaryForm(instance=bens,)
		
		if dform.is_valid():
			if request.POST.get('search'):
				if (dform.cleaned_data['to_date']-dform.cleaned_data['from_date']).days<0:
					messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
					return HttpResponseRedirect(reverse('edit_beneficiary',kwargs={'ben_id':ben_id}))
				else :
					return HttpResponseRedirect(reverse('view_beneficiary_history',
						kwargs={'from_d':dform.cleaned_data['from_date'].strftime('%m%d%Y'),
							'to_d':dform.cleaned_data['to_date'].strftime('%m%d%Y'),
							'ben_id':bens.id}))
			else:
				ext={'from_date':(dform.cleaned_data['from_date'].month,dform.cleaned_data['from_date'].year,dform.cleaned_data['from_date'].day),
						'to_date':(dform.cleaned_data['to_date'].month,dform.cleaned_data['to_date'].year,dform.cleaned_data['to_date'].day),}
				pf=dform.cleaned_data['prevtime_f']
				pt=dform.cleaned_data['prevtime_t']
				if pf is not None and pt is not None:
					tmpt=datetime.strptime(pt,'%m%d%Y')
					tmpf=datetime.strptime(pf,'%m%d%Y')
					if dform.cleaned_data['to_date'].month!=tmpt.month or dform.cleaned_data['to_date'].year!=tmpt.year:
						ext['to_date']=(dform.cleaned_data['to_date'].month,dform.cleaned_data['to_date'].year,1)
					elif dform.cleaned_data['from_date'].month!=tmpf.month or dform.cleaned_data['from_date'].year!=tmpf.year:
						ext['from_date']=(dform.cleaned_data['from_date'].month,dform.cleaned_data['from_date'].year,1)
				dform= ActivityDateForm(
						extra=ext
				)
				
	else:
		dform=ActivityDateForm(extra=None)
		bform=BeneficiaryForm(instance=bens)

	return render(request,template,{'conf':conf,'dform':dform,'bform':bform,'title':'edit beneficiary','ben_id':ben_id,})



@login_required
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
def beneficiary(request,template='board/beneficiary.html'):
	try:
		auser=User.objects.get(id=request.user.id)
	except ObjectDoesNotExist:
		raise Http404

	if auser.is_superuser:
		bens=Beneficiary.objects.all()
	else:
		bens=auser.beneficiaries.all()
	
	ty=Beneficiary.B_TYPE[0][0]
	capsule=[]
	if request.method=='POST':
		if 'add' in request.POST:
			bform=BeneficiaryForm(request.POST)
			form=BeneficiaryTypeForm(initial={'ty':ty})
			if bform.is_valid():
				b=bform.save(commit=False)
				b.user=request.user
				b.save()
				messages.add_message(request,messages.SUCCESS,'The data have been successfully added.')
				return HttpResponseRedirect(reverse('beneficiary'))

		else:
			bform=BeneficiaryForm()
			form=BeneficiaryTypeForm(request.POST)
			if form.is_valid():
				ty=form.cleaned_data['ty']

	else:
		ty=request.GET.get('ty',ty)
		form=BeneficiaryTypeForm(initial={'ty':ty})
		bform=BeneficiaryForm()
		
	for ben in bens.filter(ty=ty):
		center=ben.user.username
		a=ben.lname
		b=ben.fname
		capsule.append({'center':center,'id':ben.id,'a':a,'b':b,})

	paginator=Paginator(capsule,10)
	page=request.GET.get('page')
	try:
		contents=paginator.page(page)
	except PageNotAnInteger:
		contents=paginator.page(1)
	except EmptyPage:
		contents=paginator.page(paginator.num_pages)

	return render(request,template,{'conf':conf,'title':'beneficiary','form':form,'bform':bform,'contents':contents,'ty':ty,})


@login_required
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
	bens=act.beneficiaries.all()
	f_d=act.fdate
	t_d=act.tdate
	bffset=modelformset_factory(Beneficiary,form=BeneficiaryForm,formset=RequiredModelFormSet,max_num=50)
	try:
		auser=User.objects.get(id=editing_user.id)
	except ObjectDoesNotExist:
		raise Http404
	data={}
	for b in auser.beneficiaries.all():
		dic={'id':b.id,'lname':b.lname,'fname':b.fname,'ty':b.ty,}
		data[b.id]=dic
	data=json.dumps(data)
	
	if request.method== 'POST':
		aform=ActivityForm(request.POST,instance=act)
		bform=bffset(request.POST,queryset=bens)
		dform=ActivityDateForm(request.POST,extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})
		if dform.is_valid():

			if request.POST.get('save'):
				if (dform.cleaned_data['to_date']-dform.cleaned_data['from_date']).days<0:
					messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
					return HttpResponseRedirect(reverse('edit_activity',kwargs={'act_id':act_id}))
				elif aform.is_valid() and bform.is_valid():
					activity=aform.save(commit=False)
					activity.fdate=dform.cleaned_data['from_date']
					activity.tdate=dform.cleaned_data['to_date']
					activity.save()
					aform.save_m2m()

					for b in bens:
						act.beneficiaries.remove(b)

					for form in bform.forms:
						if form.cleaned_data['id'] is None and form.cleaned_data['temp_id'] is None:
							b=form.save(commit=False)
							b.user=editing_user
							b.save()
							form.save_m2m()
							b.activity.add(activity)
						else:
							form_id=form.cleaned_data['temp_id'] or form.cleaned_data['id'].id
							try:
								b=Beneficiary.objects.get(id=form_id,user=editing_user)
							except:
								continue
							else:
								b.lname=form.cleaned_data['lname']
								b.fname=form.cleaned_data['fname']
								b.ty=form.cleaned_data['ty']
								b.save()
								b.activity.add(activity)

					messages.add_message(request,messages.SUCCESS,'The data have been successfully edited.')
					return HttpResponseRedirect(reverse('edit_activity',kwargs={'act_id':act_id}))
				messages.add_message(request,messages.WARNING,bform.non_form_errors())
			else:
				ext={'from_date':(dform.cleaned_data['from_date'].month,dform.cleaned_data['from_date'].year,dform.cleaned_data['from_date'].day),
						'to_date':(dform.cleaned_data['to_date'].month,dform.cleaned_data['to_date'].year,dform.cleaned_data['to_date'].day),}
				pf=dform.cleaned_data['prevtime_f']
				pt=dform.cleaned_data['prevtime_t']
				if pf is not None and pt is not None:
					tmpt=datetime.strptime(pt,'%m%d%Y')
					tmpf=datetime.strptime(pf,'%m%d%Y')
					if dform.cleaned_data['to_date'].month!=tmpt.month or dform.cleaned_data['to_date'].year!=tmpt.year:
						ext['to_date']=(dform.cleaned_data['to_date'].month,dform.cleaned_data['to_date'].year,1)
					elif dform.cleaned_data['from_date'].month!=tmpf.month or dform.cleaned_data['from_date'].year!=tmpf.year:
						ext['from_date']=(dform.cleaned_data['from_date'].month,dform.cleaned_data['from_date'].year,1)
				dform= ActivityDateForm(
						extra=ext
				)
				
	else:
		aform=ActivityForm(instance=act)
		bform=bffset(queryset=bens)
		dform=ActivityDateForm(extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})

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
		acts=Activity.objects.all()
	else:
		acts=auser.activities.all()
	

	capsule=[]
	for ac in acts.filter(fdate__gte=f_d,tdate__lte=t_d):
		center=ac.user.username
		a=dict(Activity.A_TYPE)[ac.activity_ty]
		b=ac.beneficiaries.filter(ty=1).count()
		c=ac.beneficiaries.filter(ty=2).count()
		d=0
		capsule.append({'center':center,'id':ac.id,'a':a,'b':b,'c':c,'d':d,})

	form=ActivityDateForm(extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),'editable':False,},)
	paginator=Paginator(capsule,10)
	page=request.GET.get('page')
	try:
		contents=paginator.page(page)
	except PageNotAnInteger:
		contents=paginator.page(1)
	except EmptyPage:
		contents=paginator.page(paginator.num_pages)

	return render(request,template,{'conf':conf,'form':form,'contents':contents,'title':'view activity',})







@login_required
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
	for b in auser.beneficiaries.all():
		dic={'id':b.id,'lname':b.lname,'fname':b.fname,'ty':b.ty,}
		data[b.id]=dic
	data=json.dumps(data)
	bffset=formset_factory(BeneficiaryForm,max_num=50,formset=RequiredFormSet)
	if request.method== 'POST':
		aform=ActivityForm(request.POST)
		bform=bffset(request.POST)
		dform=ActivityDateForm(request.POST,extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})
		if dform.is_valid():

			if request.POST.get('save'):
				if (dform.cleaned_data['to_date']-dform.cleaned_data['from_date']).days<0:
					messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
					return HttpResponseRedirect(reverse('add_activity',kwargs={'from_d':dform.cleaned_data['from_date'].strftime('%m%d%Y'),
						'to_d':dform.cleaned_data['to_date'].strftime('%m%d%Y')}))
				elif aform.is_valid() and bform.is_valid():					
					activity=aform.save(commit=False)
					activity.user=request.user
					activity.fdate=dform.cleaned_data['from_date']
					activity.tdate=dform.cleaned_data['to_date']
					activity.save()
					aform.save_m2m()
					for form in bform.forms:
						if form.cleaned_data['temp_id'] is None:
							b=form.save(commit=False)
							b.user=request.user
							b.save()
							form.save_m2m()
							b.activity.add(activity)
						else:
							try:
								b=Beneficiary.objects.get(id=form.cleaned_data['temp_id'],user=request.user)
							except:
								continue
							else:
								b.lname=form.cleaned_data['lname']
								b.fname=form.cleaned_data['fname']
								b.ty=form.cleaned_data['ty']
								b.save()
								b.activity.add(activity)

					messages.add_message(request,messages.SUCCESS,'The data have been successfully added.')
					return HttpResponseRedirect(reverse('activity'))
				messages.add_message(request,messages.WARNING,bform.non_form_errors())

			else:
				ext={'from_date':(dform.cleaned_data['from_date'].month,dform.cleaned_data['from_date'].year,dform.cleaned_data['from_date'].day),
						'to_date':(dform.cleaned_data['to_date'].month,dform.cleaned_data['to_date'].year,dform.cleaned_data['to_date'].day),}
				pf=dform.cleaned_data['prevtime_f']
				pt=dform.cleaned_data['prevtime_t']
				if pf is not None and pt is not None:
					tmpt=datetime.strptime(pt,'%m%d%Y')
					tmpf=datetime.strptime(pf,'%m%d%Y')
					if dform.cleaned_data['to_date'].month!=tmpt.month or dform.cleaned_data['to_date'].year!=tmpt.year:
						ext['to_date']=(dform.cleaned_data['to_date'].month,dform.cleaned_data['to_date'].year,1)
					elif dform.cleaned_data['from_date'].month!=tmpf.month or dform.cleaned_data['from_date'].year!=tmpf.year:
						ext['from_date']=(dform.cleaned_data['from_date'].month,dform.cleaned_data['from_date'].year,1)
				dform= ActivityDateForm(
						extra=ext
				)
				
	else:
		aform=ActivityForm()
		bform=bffset()
		dform=ActivityDateForm(extra={
			'from_date':(f_d.month,f_d.year,f_d.day),
			'to_date':(t_d.month,t_d.year,t_d.day),})

	return render(request,template,{'conf':conf,'dform':dform,'aform':aform,'bform':bform,'title':'add activity'
		,'from_d':from_d,'to_d':to_d,'data':data,})




@login_required
def activity(request,template='board/activity.html'):
	if request.method == 'POST':
		if 'add-from_date_0' in request.POST:
			add_form = ActivityDateForm(request.POST,extra=None,prefix="add")
			view_form= ActivityDateForm(extra=None,prefix="view")
			if add_form.is_valid():
				if request.POST.get('add'):
					if (add_form.cleaned_data['to_date']-add_form.cleaned_data['from_date']).days<0:
						messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
						return HttpResponseRedirect(reverse('activity'))
					else :
						return HttpResponseRedirect(reverse('add_activity',kwargs={'from_d':add_form.cleaned_data['from_date'].strftime('%m%d%Y'),
							'to_d':add_form.cleaned_data['to_date'].strftime('%m%d%Y')}))
				else:
					ext={'from_date':(add_form.cleaned_data['from_date'].month,add_form.cleaned_data['from_date'].year,add_form.cleaned_data['from_date'].day),
						'to_date':(add_form.cleaned_data['to_date'].month,add_form.cleaned_data['to_date'].year,add_form.cleaned_data['to_date'].day),}
					
					pf=add_form.cleaned_data['prevtime_f']
					pt=add_form.cleaned_data['prevtime_t']
					if pf is not None and pt is not None:
						tmpt=datetime.strptime(pt,'%m%d%Y')
						tmpf=datetime.strptime(pf,'%m%d%Y')
						
						if add_form.cleaned_data['to_date'].month!=tmpt.month or add_form.cleaned_data['to_date'].year!=tmpt.year:
							ext['to_date']=(add_form.cleaned_data['to_date'].month,add_form.cleaned_data['to_date'].year,1)
						elif add_form.cleaned_data['from_date'].month!=tmpf.month or add_form.cleaned_data['from_date'].year!=tmpf.year:
							ext['from_date']=(add_form.cleaned_data['from_date'].month,add_form.cleaned_data['from_date'].year,1)
					
					add_form= ActivityDateForm(
							extra=ext,prefix="add"
					)
		elif 'view-from_date_0' in request.POST:
			add_form = ActivityDateForm(extra=None,prefix="add")
			view_form= ActivityDateForm(request.POST,extra=None,prefix="view")
			if view_form.is_valid():
				if request.POST.get('view'):
					if (view_form.cleaned_data['to_date']-view_form.cleaned_data['from_date']).days<0:
						messages.add_message(request,messages.WARNING,'From date and To date must be in chronological order.')
						return HttpResponseRedirect(reverse('activity'))
					else :
						return HttpResponseRedirect(reverse('view_activity',kwargs={'from_d':view_form.cleaned_data['from_date'].strftime('%m%d%Y'),
							'to_d':view_form.cleaned_data['to_date'].strftime('%m%d%Y')}))
				else:
					ext={'from_date':(view_form.cleaned_data['from_date'].month,view_form.cleaned_data['from_date'].year,view_form.cleaned_data['from_date'].day),
						'to_date':(view_form.cleaned_data['to_date'].month,view_form.cleaned_data['to_date'].year,view_form.cleaned_data['to_date'].day),}
					pf=view_form.cleaned_data['prevtime_f']
					pt=view_form.cleaned_data['prevtime_t']
					if pf is not None and pt is not None:
						tmpt=datetime.strptime(pt,'%m%d%Y')
						tmpf=datetime.strptime(pf,'%m%d%Y')
						if view_form.cleaned_data['to_date'].month!=tmpt.month or view_form.cleaned_data['to_date'].year!=tmpt.year:
							ext['to_date']=(view_form.cleaned_data['to_date'].month,view_form.cleaned_data['to_date'].year,1)
						elif view_form.cleaned_data['from_date'].month!=tmpf.month or view_form.cleaned_data['from_date'].year!=tmpf.year:
							ext['from_date']=(view_form.cleaned_data['from_date'].month,view_form.cleaned_data['from_date'].year,1)
					view_form= ActivityDateForm(
							extra=ext,prefix="view"
					)
		
	else :
		add_form = ActivityDateForm(extra=None,prefix="add")
		view_form= ActivityDateForm(extra=None,prefix="view")
	return render(request,template,{'conf':conf,'add_form':add_form,'view_form':view_form,'title':'activity'})
