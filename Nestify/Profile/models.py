from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from Family import models as fModels

class CustomUser(AbstractUser):
    birth = models.DateField(default=None, blank=True, null=True)

    def getFamily(self):
        try:
            return fModels.FamilyMember.objects.get(user=self, accepted=True).family
        except ObjectDoesNotExist:
            return None

class Family(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Families"

class FamilyMember(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='family_member')
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='members')
    is_admin = models.BooleanField(default=False)
    is_kid = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.family.name})"

class InvitationCode(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='invitation_codes')
    code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Invitation for {self.family.name} ({self.code})"

    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()

    class Meta:
        verbose_name_plural = "Invitation Codes"
