from django.db import models
from .enum import ActivityType
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from List import models as lModels
from django.utils import timezone

# Create your models here.


class Plan(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    datetime = models.DateTimeField(default=timezone.now)
    image = models.ImageField(upload_to="plans/", blank=True, null=True)
    creator = models.ForeignKey(
        "Profile.CustomUser",
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    plan_type = models.CharField(
        max_length=20,
        choices=ActivityType.choices(),
        default=ActivityType.OTHER.name)

    class Meta:
        verbose_name = _("Plan")
        verbose_name_plural = _("Plans")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Plan_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_family_plans(family):
        return Plan.objects.filter(family=family)

    def get_list(self):
        return lModels.List.objects.filter(plan=self).first()

    def get_list_item(self):
        return lModels.ListItem.get_list_items(self.get_list())


class PlanMember(models.Model):
    plan = models.ForeignKey("Plan.Plan", on_delete=models.CASCADE)
    user = models.ForeignKey("Family.FamilyMember", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("PlanMember")
        verbose_name_plural = _("PlanMembers")

    def __str__(self):
        return f"{self.plan.name}: {self.user.user.first_name}"

    def get_absolute_url(self):
        return reverse("PlanMember_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_plan_members(plan):
        return PlanMember.objects.filter(plan=plan)
