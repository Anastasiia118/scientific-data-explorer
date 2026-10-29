from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# The refresh token lives in a cookie instead of the response body:
# - httponly: JavaScript cannot read it, so an injected script cannot steal it
# - samesite=Strict: other sites cannot make the browser send it
# - path: the browser only sends it to the auth endpoints, not to every request
REFRESH_COOKIE = 'refresh_token'
REFRESH_COOKIE_PATH = '/api/auth/'


class HasCsrfHeader(BasePermission):
    """
    CSRF protection for the cookie-based auth endpoints. A form on another site
    cannot set custom headers, and fetch() with one needs a CORS preflight,
    which this API does not allow. SameSite alone does not cover sibling
    subdomains, which count as the same site.
    """

    message = 'Missing X-Requested-With header.'

    def has_permission(self, request, view):
        return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def set_refresh_cookie(response, token):
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        max_age=int(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME'].total_seconds()),
        httponly=True,
        # HTTPS only in production; the dev server runs on plain HTTP.
        secure=not settings.DEBUG,
        samesite='Strict',
        path=REFRESH_COOKIE_PATH,
    )


class LoginView(TokenObtainPairView):
    """
    POST /auth/login/   {"username", "password"} -> {"access"} + refresh cookie
    Wrong credentials are a 401; more than 10 attempts a minute are a 429.
    """

    permission_classes = (HasCsrfHeader,)
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = 'login'

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        set_refresh_cookie(response, response.data.pop('refresh'))
        return response


class RefreshView(TokenRefreshView):
    """
    POST /auth/refresh/   refresh cookie -> {"access"} + a new refresh cookie
    The old refresh token is blacklisted; a missing, expired or reused one is a 401.
    """

    permission_classes = (HasCsrfHeader,)

    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get(REFRESH_COOKIE)
        if not token:
            raise InvalidToken('No refresh token.')

        serializer = self.get_serializer(data={'refresh': token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0]) from e
        except ObjectDoesNotExist as e:
            # simplejwt looks the user up with .get(); a deleted user would be a 500.
            raise InvalidToken('User not found.') from e

        response = Response({'access': serializer.validated_data['access']})
        set_refresh_cookie(response, serializer.validated_data['refresh'])
        return response


class LogoutView(APIView):
    """
    POST /auth/logout/   blacklists the refresh token and deletes the cookie (204)
    Always succeeds, so logging out twice is not an error.
    """

    authentication_classes = ()
    permission_classes = (HasCsrfHeader,)

    def post(self, request):
        token = request.COOKIES.get(REFRESH_COOKIE)
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                pass  # expired or already blacklisted: nothing left to revoke

        response = Response(status=status.HTTP_204_NO_CONTENT)
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH, samesite='Strict')
        return response
