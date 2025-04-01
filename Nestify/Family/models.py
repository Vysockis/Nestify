import random
import string
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse


# Create your models here.
class Family(models.Model):
    name = models.CharField(max_length=50, blank=False, null=False)
    creator = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Family")
        verbose_name_plural = _("Families")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("Family_detail", kwargs={"pk": self.pk})

    def get_family_members(self):
        return FamilyMember.objects.filter(family=self, accepted=True)


class FamilyMember(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    user = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE)
    admin = models.BooleanField(default=False)
    kid = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Family member")
        verbose_name_plural = _("Family members")

    def __str__(self):
        return f"{self.family.name}: {self.user.first_name}"

    def get_absolute_url(self):
        return reverse("FamilyMember_detail", kwargs={"pk": self.pk})


class FamilyRoom(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)

    class Meta:
        verbose_name = _("Family Room")
        verbose_name_plural = _("Family Rooms")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("FamilyRoom_detail", kwargs={"pk": self.pk})


class FamilyCode(models.Model):
    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE)
    user = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE, blank=True, null=True)
    code = models.CharField(max_length=6, unique=True, editable=False)
    used = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("Family Code")
        verbose_name_plural = _("Family Codes")

    def __str__(self):
        return self.code

    def get_absolute_url(self):
        return reverse("FamilyCode_detail", kwargs={"pk": self.pk})

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
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not FamilyCode.objects.filter(code=code).exists():
                return code


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('invite', 'Family Invitation'),
        ('request', 'Join Request'),
        ('system', 'System Notification'),
        ('general', 'General Notification'),
    ]

    family = models.ForeignKey("Family.Family", on_delete=models.CASCADE, related_name='notifications')
    recipient = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE, related_name='received_notifications')
    sender = models.ForeignKey("Profile.CustomUser", on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
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

    def get_absolute_url(self):
        return reverse("Notification_detail", kwargs={"pk": self.pk})

    def mark_as_read(self):
        self.is_read = True
        self.save()

    @classmethod
    def create_notification(cls, family, recipient, notification_type, title, message, sender=None, related_object_id=None):
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
