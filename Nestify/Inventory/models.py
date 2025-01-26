from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ItemCategory(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    default_exp = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Category_detail", kwargs={"pk": self.pk})


class ItemSubCategory(models.Model):
    category = models.ForeignKey("Inventory.ItemCategory", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    default_exp = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("SubCategory")
        verbose_name_plural = _("SubCategories")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("SubCategory_detail", kwargs={"pk": self.pk})


class Item(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField()
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    statistics_qty = models.IntegerField(default=0)
    subcategory = models.ForeignKey("Inventory.ItemSubCategory", on_delete=models.DO_NOTHING)

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Item_detail", kwargs={"pk": self.pk})


class ItemOperation(models.Model):
    item = models.ForeignKey("Inventory.Item", on_delete=models.CASCADE)
    qty = models.IntegerField(default=1)
    buy_date = models.DateField(auto_now=False, auto_now_add=True)
    exp_date = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("ItemOperation")
        verbose_name_plural = _("ItemOperations")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("ItemOperation_detail", kwargs={"pk": self.pk})
