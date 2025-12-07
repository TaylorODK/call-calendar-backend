from datetime import timedelta

import pytest
from django.utils import timezone
from users.models import LoginCode, User


@pytest.fixture
def new_code():
    return LoginCode.objects.create(
        code="1234",
        email="test_email1@ylab.team",
    )


@pytest.fixture(autouse=True)
def celery_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture
def active_user():
    return User.objects.create(
        email="test_email1@ylab.team",
        telegram_id="123456",
        is_active=True,
    )


@pytest.fixture
def not_active_user():
    return User.objects.create(
        email="test_email1@ylab.team",
        telegram_id="123456",
    )


@pytest.fixture
def old_code():
    expired_time = timezone.now() - timedelta(minutes=11)
    code = LoginCode.objects.create(
        code="1234",
        email="test_email1@ylab.team",
    )
    LoginCode.objects.filter(id=code.pk).update(
        updated_at=expired_time,
    )
    code.refresh_from_db()
    return code
