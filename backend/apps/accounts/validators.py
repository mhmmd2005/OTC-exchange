from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if not any(char.isupper() for char in password):
            raise ValidationError("Password must contain at least one uppercase English letter.")
        if not any(char.islower() for char in password):
            raise ValidationError("Password must contain at least one lowercase English letter.")
        if not any(char.isdigit() for char in password):
            raise ValidationError("Password must contain at least one number.")
        if not any(not char.isalnum() for char in password):
            raise ValidationError("Password must contain at least one special character.")

    def get_help_text(self):
        return "Password must be at least 8 characters, with uppercase, lowercase, number, and special character."
