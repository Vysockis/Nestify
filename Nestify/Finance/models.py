from decimal import Decimal
from django.db import models
from django.urls import reverse
from .enum import WalletType
from django.utils.translation import gettext_lazy as _

# Create your models here.
class Wallet(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    wallet_type = models.CharField(
        max_length=20,
        choices=WalletType.choices(),
        default=WalletType.MAIN,  # Use the name of the enum
    )

    class Meta:
        verbose_name = _("Wallet")
        verbose_name_plural = _("Wallets")

    def __str__(self):
        return f"{self.family.name}: {self.wallet_type}"

    def get_absolute_url(self):
        return reverse("Wallet_detail", kwargs={"pk": self.pk})


class Pocket(models.Model):
    wallet = models.ForeignKey("Finance.Wallet", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0))

    class Meta:
        verbose_name = _("Pocket")
        verbose_name_plural = _("Pockets")

    def __str__(self):
        return f"{self.wallet.family.name}: {self.name}"

    def get_absolute_url(self):
        return reverse("Pocket_detail", kwargs={"pk": self.pk})

class Transaction(models.Model):
    deposit = models.BooleanField(default=False)
    wallet = models.ForeignKey("Finance.Wallet", on_delete=models.CASCADE)
    pocket = models.ForeignKey("Finance.Pocket", verbose_name=_(""), on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")

    def __str__(self):
        if self.deposit:
            return f"{self.wallet.family.name}: {self.amount}, {self.wallet} -> {self.pocket.name}"

        return f"{self.wallet.family.name}: {self.amount}, {self.pocket.name} -> {self.wallet}"

    def get_absolute_url(self):
        return reverse("Transaction_detail", kwargs={"pk": self.pk})


class Category(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default="#FFFFFF")  # Default white color

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categorys")

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        return reverse("Category_detail", kwargs={"pk": self.pk})
