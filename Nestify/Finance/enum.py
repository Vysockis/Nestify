from enum import Enum
from django.utils.translation import gettext_lazy as _

class WalletType(Enum):
    MAIN = _("Main")
    SAVING = _("Saving")

    @classmethod
    def choices(cls):
        """Return choices as a tuple suitable for Django model fields."""
        return [(item.name, item.value) for item in cls]
