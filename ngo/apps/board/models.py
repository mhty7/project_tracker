from django.db import models
from django.contrib.auth.models import User

class Activity(models.Model):
	A_TYPE=(
		('1','Outreach'),
		('2','Get-Together'),
		('3','Circle'),
		('4','Formative Talk'),
		('5','Basic Course'),
		('6','Excursion'),
		('7','Mentoring'),
		('8','Others'),
	)
	user=models.ForeignKey(User,related_name='activities')
	activity_ty=models.CharField(max_length=1,choices=A_TYPE,default=1,verbose_name = "Activity Type")
	description = models.CharField(max_length=255,verbose_name = "Description")
	income = models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Income")
	fdate = models.DateField(verbose_name = "From Date")
	tdate = models.DateField(verbose_name = "To Date")
	staff_exp =models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Staff Expense")
	materials_exp=models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Material Expense")
	transp_exp=models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Transportation Expense")
	other_exp=models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Other expense")

	def __str__(self):
		return u'%s: %s' % (self.activity_ty,self.description)

	

class Beneficiary(models.Model):
	B_TYPE=(
		('1','direct'),
		('2','indirect'),
	)
	user=models.ForeignKey(User,related_name='beneficiaries')
	activity=models.ManyToManyField(Activity,related_name='beneficiaries')
	ty=models.CharField(max_length=1,choices=B_TYPE,default=1,verbose_name = "Type")
	lname=models.CharField(max_length=50,verbose_name = "Last Name")
	fname=models.CharField(max_length=50,verbose_name = "First Name")
	def __str__(self):
		return u'%s %s' % (self.fname,self.lname)
