from django.db import models
from django.contrib.auth.models import User

class CenterProfile(models.Model):
	center=models.OneToOneField(User)

	def __str__(self):
		return self.center
