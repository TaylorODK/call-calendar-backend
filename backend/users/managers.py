from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, telegram_id, password=None, **extra_fields):
        if not email:
            raise ValueError("У пользователя должен быть email")
        if not telegram_id:
            raise ValueError("У пользователя должен быть telegram_id")

        email = self.normalize_email(email)
        user = self.model(email=email, telegram_id=telegram_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, telegram_id, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(email, telegram_id, password, **extra_fields)
