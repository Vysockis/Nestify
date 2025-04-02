from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .enum import ListType

# Create your models here.
class List(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    creator = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    finished = models.BooleanField(default=False)
    plan = models.ForeignKey("Plan.Plan", on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey("Finance.Category", on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receipt_pdf = models.FileField(upload_to='receipts/', blank=True, null=True)
    list_type = models.CharField(max_length=20, choices=ListType.choices(), default=ListType.OTHER.name)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("FamilyList")
        verbose_name_plural = _("FamilyLists")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("FamilyList_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_family_list(family):
        return List.objects.filter(family=family)

    @staticmethod
    def get_family_list_finance(family):
        return List.objects.filter(family=family, list_type=ListType.FINANCE.name)


class ListItem(models.Model):
    list = models.ForeignKey("List.List", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    qty = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    item = models.ForeignKey("Inventory.Item", on_delete=models.DO_NOTHING, null=True, blank=True)
    completed = models.BooleanField(default=False)
    assigned_to = models.ForeignKey("Profile.CustomUser", on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = _("ListItem")
        verbose_name_plural = _("ListItems")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ListItem_detail", kwargs={"pk": self.pk})

    @staticmethod
    def get_list_items(list):
        return ListItem.objects.filter(list=list)
