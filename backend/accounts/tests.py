from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from .views import REFRESH_COOKIE, REFRESH_COOKIE_PATH


class AuthApiTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='ana', password='s3cret-pass')
        # Login throttling counts in the cache, which outlives a single test.
        cache.clear()
        # Sent by the frontend with every auth request (CSRF protection).
        self.client.credentials(HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    def login(self, password='s3cret-pass'):
        return self.client.post(
            reverse('auth-login'), {'username': 'ana', 'password': password}, format='json'
        )

    def refresh(self):
        return self.client.post(reverse('auth-refresh'))

    def test_login_returns_access_token_and_sets_refresh_cookie(self):
        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The refresh token is only in the cookie, never in the body.
        self.assertEqual(set(response.data), {'access'})
        self.assertEqual(AccessToken(response.data['access'])['user_id'], str(self.user.id))

        cookie = response.cookies[REFRESH_COOKIE]
        self.assertTrue(cookie['httponly'])
        self.assertEqual(cookie['samesite'], 'Strict')
        self.assertEqual(cookie['path'], REFRESH_COOKIE_PATH)

    def test_login_with_wrong_password_is_401_without_cookie(self):
        response = self.login(password='wrong')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn(REFRESH_COOKIE, response.cookies)

    def test_refresh_returns_new_access_token_and_rotates_cookie(self):
        old_refresh = self.login().cookies[REFRESH_COOKIE].value

        response = self.refresh()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {'access'})
        self.assertNotEqual(response.cookies[REFRESH_COOKIE].value, old_refresh)

    def test_used_refresh_token_cannot_be_reused(self):
        old_refresh = self.login().cookies[REFRESH_COOKIE].value
        self.refresh()

        self.client.cookies[REFRESH_COOKIE] = old_refresh
        response = self.refresh()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_without_cookie_is_401(self):
        response = self.refresh()

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_deletes_cookie_and_revokes_refresh_token(self):
        old_refresh = self.login().cookies[REFRESH_COOKIE].value

        response = self.client.post(reverse('auth-logout'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.cookies[REFRESH_COOKIE].value, '')

        self.client.cookies[REFRESH_COOKIE] = old_refresh
        self.assertEqual(self.refresh().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_cookie_succeeds(self):
        response = self.client.post(reverse('auth-logout'))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_after_refresh_revokes_the_rotated_token(self):
        self.login()
        new_refresh = self.refresh().cookies[REFRESH_COOKIE].value

        self.client.post(reverse('auth-logout'))

        self.client.cookies[REFRESH_COOKIE] = new_refresh
        self.assertEqual(self.refresh().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_refresh_token_is_401(self):
        token = RefreshToken.for_user(self.user)
        token.set_exp(lifetime=-timedelta(seconds=1))
        self.client.cookies[REFRESH_COOKIE] = str(token)

        self.assertEqual(self.refresh().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_in_refresh_cookie_is_401(self):
        self.client.cookies[REFRESH_COOKIE] = self.login().data['access']

        self.assertEqual(self.refresh().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_for_inactive_user_is_401(self):
        self.login()
        self.user.is_active = False
        self.user.save()

        self.assertEqual(self.refresh().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_for_deleted_user_is_401(self):
        self.login()
        self.user.delete()

        self.assertEqual(self.refresh().status_code, status.HTTP_401_UNAUTHORIZED)

    def test_auth_endpoints_require_csrf_header(self):
        self.login()
        self.client.credentials()  # drop the header

        for name in ['auth-login', 'auth-refresh', 'auth-logout']:
            with self.subTest(name):
                response = self.client.post(reverse(name))
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # The rejected logout did not revoke the token.
        self.client.credentials(HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(self.refresh().status_code, status.HTTP_200_OK)

    def test_login_is_throttled_after_10_attempts_a_minute(self):
        for _ in range(10):
            self.login(password='wrong')

        response = self.login()

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
