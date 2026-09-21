from django.contrib.auth.base_user import BaseUserManager


class AdminUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(
                "ایمیل الزامی است."
            )

        email = (
            self.normalize_email(email)
            .strip()
            .lower()
        )

        admin_user = self.model(
            email=email,
            **extra_fields,
        )

        if password:
            admin_user.set_password(password)
        else:
            admin_user.set_unusable_password()

        admin_user.save(
            using=self._db,
        )

        return admin_user

    def create_super_admin(
        self,
        email,
        password,
        **extra_fields,
    ):
        extra_fields.setdefault(
            "role",
            "super_admin",
        )

        return self.create_user(
            email=email,
            password=password,
            **extra_fields,
        )