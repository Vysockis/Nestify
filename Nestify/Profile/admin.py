from django.contrib import admin
from . import models
from django.contrib.auth.admin import UserAdmin

# Register your models here.


class ProfileUserAdmin(UserAdmin):
    # Add your custom fields to the fieldsets or add_fieldsets attribute
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': (
            'birth',)}),
    )


admin.site.register(models.CustomUser, ProfileUserAdmin)
