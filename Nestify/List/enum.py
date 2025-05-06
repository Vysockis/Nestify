from enum import Enum
from django.utils.translation import gettext_lazy as _


class ListType(Enum):
    GROCERY = _("Grocery")
    TASK = _("Task")
    MEAL = _("Meal")
    FINANCE = _("Finance")
    OTHER = _("Other")

    @classmethod
    def choices(cls):
        """Return choices as a tuple suitable for Django model fields."""
        return [(item.name, item.value) for item in cls]
