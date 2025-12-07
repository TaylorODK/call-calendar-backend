import pytest
from users.models import User
from event.models import Calendar, Event
from django.utils import timezone
from datetime import timedelta


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
def user_in_and_not_in_event_fixture():
    date_from = timezone.now() + timedelta(minutes=60)
    date_till = timezone.now() + timedelta(minutes=90)
    calendar = Calendar.objects.create(
        title="test",
        key="test_key",
    )
    user = User.objects.create(
        email="test_email1@ylab.team",
        telegram_id="123456",
        is_active=True,
        show_star_events=True,
        calendar=calendar,
    )
    event = Event.objects.create(
        uid="uid",
        date_from=date_from,
        date_till=date_till,
        title="test_user_in_this_event",
        description="description",
        url_calendar="url_calendar",
        calendar=calendar,
    )
    event_1 = Event.objects.create(
        uid="uid1",
        date_from=date_from,
        date_till=date_till,
        title="test_user_not_in_this_event",
        description="description",
        url_calendar="url_calendar",
        calendar=calendar,
    )
    event.users.add(user)
    event.refresh_from_db()
    return calendar, event, event_1, user
