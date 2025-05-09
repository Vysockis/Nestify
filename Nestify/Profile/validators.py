from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class UppercaseValidator:
    def validate(self, password, user=None):
        if not any(char.isupper() for char in password):
            raise ValidationError(
                _("Slaptažodis turi turėti bent vieną didžiąją raidę."),
                code='password_no_upper',
            )

    def get_help_text(self):
        return _("Jūsų slaptažodis turi turėti bent vieną didžiąją raidę.")


class SpecialCharacterValidator:
    def validate(self, password, user=None):
        if not any(char in "!@#$%^&*(),.?\":{}|<>" for char in password):
            raise ValidationError(
                _("Slaptažodis turi turėti bent vieną specialų simbolį."),
                code='password_no_special',
            )

    def get_help_text(self):
        return _("Jūsų slaptažodis turi turėti bent vieną specialų simbolį (!@#$%^&*(),.?\":{}|<>).") 