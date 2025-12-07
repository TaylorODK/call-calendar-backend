from http import HTTPStatus

import pytest
from django.core import mail
from users.models import LoginCode


@pytest.mark.django_db
class Test00SendCode:
    URL_PATH = "/api/users/email/"
    HEADER = {"HTTP_TELEGRAM_ID": "123456"}
    DATA_1 = {"email": "test_email1@ylab.team"}
    DATA_2 = {"email": "test_email2@ylab.team"}
    DATA_WRONG_DOMAIN = {"email": "test_email1@yla.team"}
    DATA_WRONG_FIELD_NAME = {"e-mail": "test_email1@ylab.team"}
    DATA_WRONG_TYPE_INT = {"email": 123456}
    DATA_WRONG_TYPE_STR = {"e-mail": "string"}

    def test_00_send_code_good_request(self, client):
        response = client.post(self.URL_PATH, data=self.DATA_1, **self.HEADER)
        assert response.status_code == HTTPStatus.CREATED

    def test_01_send_wrong_domain(self, client):
        response = client.post(
            self.URL_PATH, data=self.DATA_WRONG_DOMAIN, **self.HEADER
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_02_send_wrong_field_name(self, client):
        response = client.post(
            self.URL_PATH, data=self.DATA_WRONG_FIELD_NAME, **self.HEADER
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_03_send_wrong_field_type_int(self, client):
        response = client.post(
            self.URL_PATH, data=self.DATA_WRONG_TYPE_INT, **self.HEADER
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_04_send_wrong_field_type_str(self, client):
        response = client.post(
            self.URL_PATH, data=self.DATA_WRONG_TYPE_STR, **self.HEADER
        )
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_05_send_no_telegram_id(self, client):
        response = client.post(self.URL_PATH, data=self.DATA_2)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_06_send_code_not_expired_time(self, client, new_code):
        response = client.post(self.URL_PATH, data=self.DATA_1, **self.HEADER)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_07_logincode_creation(self, client):
        first_count = LoginCode.objects.count()
        client.post(self.URL_PATH, data=self.DATA_1, **self.HEADER)
        second_count = LoginCode.objects.count()
        new_code = LoginCode.objects.last()
        assert (second_count - first_count) == 1
        assert new_code.email == self.DATA_1["email"]

    def test_08_email_sent(self, client):
        mail.outbox = []
        client.post(self.URL_PATH, data=self.DATA_2, **self.HEADER)
        assert len(mail.outbox) == 1
        sent_mail = mail.outbox[0]
        assert self.DATA_2["email"] == sent_mail.to[0]
        sent_code = sent_mail.body.split(": ")[1]
        assert LoginCode.objects.last().code == sent_code

    def test_09_existing_user_email_active(self, client, active_user):
        response = client.post(self.URL_PATH, data=self.DATA_1, **self.HEADER)
        assert response.status_code == HTTPStatus.BAD_REQUEST

    def test_10_existing_user_email_not_active(self, client, not_active_user):
        response = client.post(self.URL_PATH, data=self.DATA_1, **self.HEADER)
        assert response.status_code == HTTPStatus.CREATED
