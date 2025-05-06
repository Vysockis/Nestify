from django.db import models
from Family.models import Family


class SmartDevice(models.Model):
    DEVICE_TYPES = [
        ('LIGHT', 'Light Bulb'),
        # Add more device types here as needed
    ]

    name = models.CharField(max_length=100)
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES)
    is_on = models.BooleanField(default=False)
    brightness = models.IntegerField(default=100)  # 0-100
    room = models.CharField(max_length=100)
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.get_device_type_display()})"

    class Meta:
        ordering = ['-updated_at']
