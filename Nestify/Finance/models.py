from decimal import Decimal
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

# Create your models here.
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
