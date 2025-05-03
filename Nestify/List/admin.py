from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.List)
admin.site.register(models.ListItem)
admin.site.register(models.PointsTransaction)
admin.site.register(models.PrizeTask)
admin.site.register(models.Prize)
