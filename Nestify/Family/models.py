import random
import string
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


# Create your models here.
class Family(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)
    creator = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Family")
        verbose_name_plural = _("Families")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Family_detail", kwargs={"pk": self.pk})


class FamilyMember(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    user = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)
    admin = models.BooleanField(default=False)
    kid = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Family member")
        verbose_name_plural = _("Family members")

    def __str__(self):
        return f"{self.family.name}: {self.user.first_name}"

    def get_absolute_url(self):
        return reverse("FamilyMember_detail", kwargs={"pk": self.pk})


class FamilyRoom(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = _("Family Room")
        verbose_name_plural = _("Family Rooms")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("FamilyRoom_detail", kwargs={"pk": self.pk})


class FamilyCode(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    user = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE, blank=True, null=True)
    code = models.CharField(max_length=6, unique=True, editable=False)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Family Code")
        verbose_name_plural = _("Family Codes")

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse("FamilyCode_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.code:  # Generate code only if it doesn't already exist
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def generate_unique_code(self):
        """Generate a unique 6-character alphanumeric code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not FamilyCode.objects.filter(code=code).exists():
                return code
