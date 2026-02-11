from datetime import timedelta
from django.utils import timezone
from users.v2.dto import (
    RegistrationData,
    RegistrationAnswer,
    RegistrationError,
)
from users.models import User, LoginCode
from core.constants import ALLOWED_EMAIL, CODE_EXPIRATION_TIME
from core.enums import ErrorCodes


class RegistrationService:
    def __call__(
        self,
        registration_data: RegistrationData,
    ) -> RegistrationAnswer:
        checks = (
            self._check_telegram_id,
            self._check_email_user,
            self._check_email_domain,
            self._check_last_code,
        )
        for check in checks:
            error = check(registration_data=registration_data)
            if error:
                return RegistrationAnswer(
                    error=error,
                    can_send_code=False,
                )
        return RegistrationAnswer(
            error=None,
            can_send_code=True,
        )

    def _check_telegram_id(
        self,
        registration_data: RegistrationData,
    ) -> RegistrationError | None:
        if User.objects.filter(
            telegram_id=registration_data.telegram_id,
            is_active=True,
        ).exists():
            return RegistrationError(
                error_code=ErrorCodes.HAVE_ACTIVATED_USER,
                error_message="❌ Активированный пользователь с вашим"
                " telegram_id уже существует.",
            )
        return None

    def _check_email_user(
        self,
        registration_data: RegistrationData,
    ) -> RegistrationError | None:
        user = User.objects.filter(email=registration_data.email).first()
        if user and user.is_active:
            return RegistrationError(
                error_code=ErrorCodes.EMAIL_EXISTS,
                error_message="❌ Активированный пользователь с таким Email"
                " уже существует, пожалуйста, укажите другой email"
                " и воспользуйтесь командой /email",
            )
        return None

    def _check_email_domain(
        self,
        registration_data: RegistrationData,
    ) -> RegistrationError | None:
        if not any(str(registration_data.email).endswith(i) for i in ALLOWED_EMAIL):
            return RegistrationError(
                error_code=ErrorCodes.WRONG_DOMAIN,
                error_message="❌ Ваш Email должен быть в домене ylab",
            )
        return None

    def _check_last_code(
        self,
        registration_data: RegistrationData,
    ) -> RegistrationError | None:
        verification = LoginCode.objects.filter(
            email=registration_data.email,
        ).first()
        if verification:
            expiration_time = verification.updated_at + timedelta(
                minutes=CODE_EXPIRATION_TIME,
            )
            if timezone.now() < expiration_time:
                return RegistrationError(
                    error_code=ErrorCodes.CODE_NOT_EXPIRED,
                    error_message=f"❌ время действия отправленного кода"
                    f" {CODE_EXPIRATION_TIME} минут."
                    " Новый запрос команды /email можно сделать после"
                    " истечения срока действия кода",
                )
        return None
