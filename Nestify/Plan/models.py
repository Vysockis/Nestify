from django.db import models
from .enum import ActivityType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Plan(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    date = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True)
    image = models.ImageField(upload_to=None, height_field=None, width_field=None, max_length=None, blank=True, null=True)
    plan_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices(),
        default=ActivityType.OTHER.name,  # Use the name of the enum
    )

    class Meta:
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Plan_detail", kwargs={"pk": self.pk})

class PlanMember(models.Model):
    plan = models.ForeignKey("Plan.Plan", on_delete=models.CASCADE)
    user = models.ForeignKey("Family.FamilyMember", verbose_name=_(""), on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("PlanMember")
        verbose_name_plural = _("PlanMembers")

    def __str__(self):
        return f"{self.plan.name}: {self.user.user.first_name}"

    def get_absolute_url(self):
        return reverse("PlanMember_detail", kwargs={"pk": self.pk})
