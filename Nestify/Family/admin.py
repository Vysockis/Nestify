from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Family)
admin.site.register(models.FamilyMember)
admin.site.register(models.FamilyCode)
admin.site.register(models.Notification)
admin.site.register(models.FamilySettings)
