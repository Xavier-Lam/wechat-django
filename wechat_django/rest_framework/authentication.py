try:
    from rest_framework.authentication import BaseAuthentication  # noqa
except ImportError:
    class BaseAuthentication:
        """
        All authentication classes should extend BaseAuthentication.
        """

        def authenticate(self, request):
            """
            Authenticate the request and return a two-tuple of (user, token).
            """
            raise NotImplementedError(".authenticate() must be overridden.")

        def authenticate_header(self, request):
            """
            Return a string to be used as the value of the `WWW-Authenticate`
            header in a `401 Unauthenticated` response, or `None` if the
            authentication scheme should return `403 Permission Denied`
            responses.
            """
            pass
