import pytest

from http import HTTPStatus


@pytest.mark.django_db
class Test02Event:
    URL_PATH = "/api/meetings/"
    HEADER = {"HTTP_TELEGRAM_ID": "123456"}

    def test_00_telegram_client_request(self, client, active_user):
        response = client.get(self.URL_PATH, **self.HEADER)
        assert response.status_code == HTTPStatus.OK

    def test_01_not_active_user(self, client, not_active_user):
        response = client.get(self.URL_PATH, **self.HEADER)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_02_no_header_request(self, client, active_user):
        response = client.get(self.URL_PATH)
        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_03_user_in_event_show(self, client, user_in_and_not_in_event_fixture):
        response = client.get(self.URL_PATH, **self.HEADER)
        event = user_in_and_not_in_event_fixture[1].title
        event_1 = user_in_and_not_in_event_fixture[2].title
        events_from_response = response.json()["meetings"]
        shown = False
        not_shown = True
        for response_event in events_from_response:
            if event == response_event["title"]:
                shown = True
            if event_1 == response_event["title"]:
                not_shown = False
        assert shown
        assert not_shown
