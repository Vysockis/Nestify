from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Family)
admin.site.register(models.FamilyMember)
admin.site.register(models.FamilyRoom)
admin.site.register(models.FamilyCode)
