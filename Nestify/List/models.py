from django.db import models
from django.urls import reverse
from .enum import ListType
from django.utils.translation import gettext_lazy as _

# Create your models here.
class List(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    creator = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)
    photo = models.ImageField(null=True, blank=True)
    finished = models.BooleanField(default=False)
    plan = models.ForeignKey("Plan.Plan", on_delete=models.CASCADE, null=True, blank=True)
    list_type = models.CharField(
        max_length=20,
        choices=ListType.choices(),
        default=ListType.OTHER.name,  # Use the name of the enum
    )
    datetime = models.DateTimeField(auto_now=False, auto_now_add=False)

    class Meta:
        verbose_name = _("FamilyList")
        verbose_name_plural = _("FamilyLists")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("FamilyList_detail", kwargs={"pk": self.pk})


class ListItem(models.Model):
    list = models.ForeignKey("List.List", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    qty = models.IntegerField(null=True, blank=True)
    item = models.ForeignKey("Inventory.Item", on_delete=models.DO_NOTHING, null=True, blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("ListItem")
        verbose_name_plural = _("ListItems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ListItem_detail", kwargs={"pk": self.pk})
