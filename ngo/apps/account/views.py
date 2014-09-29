from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth import login,authenticate,logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from ngo import conf

def user_login(request):
	if request.method == 'GET':
		return render(request,'account/login.html',{'conf':conf,'title':'log in','next':request.GET.get('next')})

	elif request.method == 'POST':
		username=request.POST.get('username')
		password = request.POST.get('password')
		next=request.POST.get('next')
		user=authenticate(username=username,password=password)

		if not User.objects.filter(username=username).exists() or user is None:
			messages.add_message(request,messages.WARNING,'failed to login.')
			return HttpResponseRedirect(reverse('login'))
		login(request,user)
		print(next)
		if next == 'None':
			return HttpResponseRedirect(reverse('index'))
		return HttpResponseRedirect(next)
		
		

def user_logout(request):
	logout(request)
	return HttpResponseRedirect(reverse('index'))