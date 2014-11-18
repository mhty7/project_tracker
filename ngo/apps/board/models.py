from django.db import models
from django.contrib.auth.models import User

WEEK_CHOICES = (
	('1', '1st'),
	('2', '2nd'),
	('3', '3rd'),
	('4', '4th'),
)

class BeneficiaryGroup(models.Model):
	name=models.CharField(max_length=50,verbose_name = "Group Name")
	user=models.ForeignKey(User,related_name='beneficiaryGroup')
	def __str__(self):
		return u'%s: %s' % (self.user,self.name)

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
	#income = models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Income")
	fdate = models.DateField(verbose_name = "From Date")
	tdate = models.DateField(verbose_name = "To Date")
	#staff_exp =models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Staff Expense")
	#materials_exp=models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Material Expense")
	#transp_exp=models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Transportation Expense")
	#other_exp=models.DecimalField(max_digits=13,decimal_places=2,verbose_name = "Other expense")

	def __str__(self):
		return u'%s' % (dict(Activity.A_TYPE)[self.activity_ty],)

	

class Beneficiary(models.Model):
	B_TYPE=(
		('1','direct'),
		('2','indirect'),
	)
	user=models.ForeignKey(User,related_name='beneficiaries')
	#this activity attribute might cause the data strorage redundant,
	#because we have AvtivityWeeklyDescription on which associated beneficiary is dangling.
	#activity=models.ManyToManyField(Activity,related_name='beneficiaries')
	group=models.ManyToManyField(BeneficiaryGroup,related_name='beneficiaries',blank=True)
	ty=models.CharField(max_length=1,choices=B_TYPE,default=1,verbose_name = "Type")
	lname=models.CharField(max_length=50,verbose_name = "Last Name")
	fname=models.CharField(max_length=50,verbose_name = "First Name")
	def __str__(self):
		return u'%s %s' % (self.fname,self.lname)

class ActivityWeeklyDescription(models.Model):
	activity=models.ForeignKey(Activity,verbose_name="Activity",related_name='description')
	week=models.CharField(max_length=1,choices=WEEK_CHOICES,verbose_name = "Week",default=1)
	description=models.CharField(max_length=255,verbose_name = "Description",blank=True,null=True)
	beneficiaries=models.ManyToManyField(Beneficiary,related_name='activityWeek',blank=True)
	class Meta:
		unique_together = (('activity','week'),)

