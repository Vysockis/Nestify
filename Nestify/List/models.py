from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.conf import settings
from .enum import ListType
from Family.models import FamilyMember

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
    datetime = models.DateTimeField(default=timezone.now)

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

class PrizeTask(models.Model):
    list_item = models.ForeignKey('ListItem', on_delete=models.CASCADE)
    family_member = models.ForeignKey('Family.FamilyMember', on_delete=models.CASCADE)
    points = models.IntegerField()
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('list_item', 'family_member')

    @staticmethod
    def get_pending_tasks(family):
        return PrizeTask.objects.filter(
            family_member__family=family,
            is_approved=False
        ).select_related('list_item', 'family_member', 'family_member__user')

class Prize(models.Model):
    family = models.ForeignKey('Family.Family', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    points_required = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    @staticmethod
    def get_family_prizes(family):
        return Prize.objects.filter(family=family, is_active=True)

class PointsTransaction(models.Model):
    TASK_COMPLETION = 'TASK'
    MANUAL_ADDITION = 'MANUAL'
    PRIZE_REDEMPTION = 'PRIZE'
    
    TRANSACTION_TYPES = [
        (TASK_COMPLETION, 'Task Completion'),
        (MANUAL_ADDITION, 'Manual Addition'),
        (PRIZE_REDEMPTION, 'Prize Redemption'),
    ]

    family_member = models.ForeignKey('Family.FamilyMember', on_delete=models.CASCADE)
    points = models.IntegerField()  # Can be negative for prize redemptions
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    reference_id = models.CharField(max_length=100, null=True, blank=True)  # For task_id or prize_id
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(null=True, blank=True)

    @staticmethod
    def get_member_points(family_member):
        total_points = PointsTransaction.objects.filter(
            family_member=family_member
        ).aggregate(total=models.Sum('points'))['total'] or 0
        return total_points

    @staticmethod
    def get_family_leaderboard(family):
        return FamilyMember.objects.filter(family=family).annotate(
            total_points=models.Sum('pointstransaction__points')
        ).order_by('-total_points')
