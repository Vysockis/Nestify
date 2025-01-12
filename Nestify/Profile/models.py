from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    birth = models.DateField(default=None, blank=True, null=True)
