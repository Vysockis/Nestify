from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist

from Family import models as fModels


class CustomUser(AbstractUser):
    birth = models.DateField(default=None, blank=True, null=True)

    def getFamily(self):
        try:
            return fModels.FamilyMember.objects.get(
                user=self, accepted=True).family
        except ObjectDoesNotExist:
            return None
