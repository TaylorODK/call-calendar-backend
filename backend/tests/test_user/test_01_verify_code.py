import pytest

from http import HTTPStatus


@pytest.mark.django_db
class Test01VerifyCode:
    URL_PATH = "/api/users/code/"
    HEADER = {"HTTP_TELEGRAM_ID": "123456"}

    def test_00_good_code_sent(self, client, new_code, not_active_user):
        code = {
            "code": new_code.code,
        }
        response = client.post(self.URL_PATH, code, **self.HEADER)
        assert response.status_code == HTTPStatus.CREATED
        not_active_user.refresh_from_db()
        assert not_active_user.is_active

    def test_01_wrong_code_sent(self, client, new_code, not_active_user):
        code = {
            "code": "new_code.code",
        }
        response = client.post(self.URL_PATH, code, **self.HEADER)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        not_active_user.refresh_from_db()
        assert not not_active_user.is_active

    def test_02_wrong_code_field(self, client, new_code, not_active_user):
        code = {
            "cote": "new_code.code",
        }
        response = client.post(self.URL_PATH, code, **self.HEADER)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        not_active_user.refresh_from_db()
        assert not not_active_user.is_active

    def test_03_expired_code(self, client, old_code, not_active_user):
        code = {
            "code": old_code.code,
        }
        response = client.post(self.URL_PATH, code, **self.HEADER)
        assert response.status_code == HTTPStatus.BAD_REQUEST
        not_active_user.refresh_from_db()
        assert not not_active_user.is_active
