from django.db.models.signals import post_save
from django.dispatch import receiver
from . import models
from List import models as lModels
from List.enum import ListType

@receiver(post_save, sender=models.Plan)
def create_list_for_plan(sender, instance, created, **kwargs):
    if created:
        lModels.List.objects.create(
            family=instance.family,
            name=f"{instance.name} - List",
            description=f"List for {instance.name}",
            creator=instance.creator,
            plan=instance,
            list_type=ListType.OTHER.name,
            datetime=instance.datetime
        )
