from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class PasswordStrengthValidator:
    """
    Validate that the password meets all requirements:
    - At least 8 characters long
    - Contains at least one letter and one number
    - Contains at least one special character
    - Not entirely numeric
    """
    
    def validate(self, password, user=None):
        errors = []
        
        if len(password) < 8:
            errors.append(_("Password must be at least 8 characters long."))
        
        if not re.search(r'[A-Za-z]', password):
            errors.append(_("Password must contain at least one letter."))
            
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one number."))
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(_("Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."))
        
        if password.isdigit():
            errors.append(_("Password cannot be entirely numeric."))
            
        if errors:
            raise ValidationError(errors)
    
    def get_help_text(self):
        return _(
            "Your password must contain at least 8 characters, "
            "including letters, numbers, and special characters."
        ) 