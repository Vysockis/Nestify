import random
import string
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


# Create your models here.
class Family(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)
    creator = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)
    is_paid = models.BooleanField(default=False)
    checkout_url = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = _("Family")
        verbose_name_plural = _("Families")

    def __str__(self):
        return self.name

    def get_family_members(self):
        return FamilyMember.objects.filter(family=self, accepted=True)

    def get_pending_members(self):
        return FamilyMember.objects.filter(family=self, accepted=False)


class FamilyMember(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    user = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)
    admin = models.BooleanField(default=False)
    kid = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    points = models.IntegerField(default=0)

    class Meta:
        verbose_name = _("Family member")
        verbose_name_plural = _("Family members")

    def __str__(self):
        return f"{self.family.name}: {self.user.first_name}"


class FamilyCode(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    user = models.ForeignKey(
        "Profile.CustomUser",
        on_delete=models.CASCADE,
        blank=True,
        null=True)
    code = models.CharField(max_length=6, unique=True, editable=False)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Family Code")
        verbose_name_plural = _("Family Codes")

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if not self.code:  # Generate code only if it doesn't already exist
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if the code is valid (not used)"""
        return not self.used

    def generate_unique_code(self):
        """Generate a unique 6-character alphanumeric code."""
        while True:
            code = ''.join(
                random.choices(
                    string.ascii_uppercase +
                    string.digits,
                    k=6))
            if not FamilyCode.objects.filter(code=code).exists():
                return code


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('invite', 'Family Invitation'),
        ('request', 'Join Request'),
        ('system', 'System Notification'),
        ('general', 'General Notification'),
        ('task_assigned', 'Task Assignment'),
    ]

    family = models.ForeignKey(
        "Family.Family",
        on_delete=models.CASCADE,
        related_name='notifications')
    recipient = models.ForeignKey(
        "Profile.CustomUser",
        on_delete=models.CASCADE,
        related_name='received_notifications')
    sender = models.ForeignKey(
        "Profile.CustomUser",
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        null=True,
        blank=True)
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField(default='')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_object_id = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['family', 'notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.notification_type}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    @classmethod
    def create_notification(
            cls,
            family,
            recipient,
            notification_type,
            title,
            message,
            sender=None,
            related_object_id=None):
        """
        Create a new notification with the given parameters.
        """
        return cls.objects.create(
            family=family,
            recipient=recipient,
            sender=sender,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_id=related_object_id
        )

    @classmethod
    def get_unread_count(cls, user):
        """
        Get the count of unread notifications for a user.
        """
        return cls.objects.filter(recipient=user, is_read=False).count()

    @classmethod
    def mark_all_as_read(cls, user, family=None):
        """
        Mark all notifications as read for a user, optionally filtered by family.
        """
        queryset = cls.objects.filter(recipient=user, is_read=False)
        if family:
            queryset = queryset.filter(family=family)
        queryset.update(is_read=True)


class FamilySettings(models.Model):
    NOTIFICATION_RECIPIENTS = [
        ('all', 'Visi šeimos nariai'),
        ('parents', 'Tik tėvai'),
        ('admin', 'Tik administratorius'),
    ]

    family = models.OneToOneField(
        "Family.Family",
        on_delete=models.CASCADE,
        related_name='settings')
    inventory_notifications = models.CharField(
        max_length=20,
        choices=NOTIFICATION_RECIPIENTS,
        default='all',
        verbose_name='Turto pranešimai'
    )
    task_notifications = models.CharField(
        max_length=20,
        choices=NOTIFICATION_RECIPIENTS,
        default='all',
        verbose_name='Užduočių pranešimai'
    )

    class Meta:
        verbose_name = "Šeimos nustatymai"
        verbose_name_plural = "Šeimos nustatymai"

    def __str__(self):
        return f"{self.family.name} nustatymai"

    @classmethod
    def get_or_create_settings(cls, family):
        settings, created = cls.objects.get_or_create(family=family)
        return settings

    def get_notification_recipients(
            self,
            notification_type,
            assigned_user=None):
        if notification_type == 'inventory':
            setting = self.inventory_notifications
            family_members = self.family.get_family_members()

            if setting == 'all':
                return [member.user for member in family_members]
            elif setting == 'parents':
                return [
                    member.user for member in family_members if not member.kid]
            else:  # admin
                return [self.family.creator]
        elif notification_type == 'task' and assigned_user:
            setting = self.task_notifications
            family_members = self.family.get_family_members()
            recipients = [assigned_user]  # Always include the assigned user

            if setting == 'all':
                recipients.extend(
                    [member.user for member in family_members if member.user != assigned_user])
            elif setting == 'parents':
                recipients.extend(
                    [member.user for member in family_members if not member.kid and member.user != assigned_user])
            elif setting == 'admin':
                if self.family.creator != assigned_user:
                    recipients.append(self.family.creator)

            return list(set(recipients))  # Remove duplicates
        return []
