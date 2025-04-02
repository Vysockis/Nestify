from django.db import models
from django.utils.translation import gettext_lazy as _

class ItemType(models.TextChoices):
    FOOD = 'FOOD', _('Maistas')
    MEDICINE = 'MEDICINE', _('Vaistai')
    CONTRACTS = 'CONTRACTS', _('Sutartys')

class Item(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    statistics_qty = models.IntegerField(default=0, null=True, blank=True)
    item_type = models.CharField(
        max_length=15,
        choices=ItemType.choices,
        default=ItemType.FOOD
    )

    class Meta:
        verbose_name = _("Item")
        verbose_name_plural = _("Items")

    def __str__(self):
        return self.name


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
        return f"{self.item.name} - {self.qty}"
