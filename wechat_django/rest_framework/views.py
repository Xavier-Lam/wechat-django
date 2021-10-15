try:
    from rest_framework.views import APIView
except ImportError:
    from django.views import View

    from . import exceptions

    class APIView(View):
        """
        A minimum implementation for drf APIView with permission and
        authentication
        """
        authentication_classes = tuple()
        permission_classes = tuple()

        def permission_denied(self, request, message=None, code=None):
            """
            If request is not permitted, determine what kind of exception to
            raise.
            """
            if request.authenticators and not request._authenticator:
                raise exceptions.NotAuthenticated()
            raise exceptions.PermissionDenied(detail=message, code=code)

        def get_authenticators(self):
            """
            Instantiates and returns the list of authenticators that this view
            can use.
            """
            return [auth() for auth in self.authentication_classes]

        def get_permissions(self):
            """
            Instantiates and returns the list of permissions that this view
            requires.
            """
            return [permission() for permission in self.permission_classes]

        def perform_authentication(self, request):
            """
            Perform authentication on the incoming request.

            Note that if you override this and simply 'pass', then
            authentication will instead be performed lazily, the first time
            either `request.user` or `request.auth` is accessed.
            """
            request._authenticator = None
            request.authenticators = self.get_authenticators()
            for authenticator in request.authenticators:
                user_auth_tuple = authenticator.authenticate(request)
                if user_auth_tuple is not None:
                    request._authenticator = authenticator
                    request.user, request.auth = user_auth_tuple
                    return
            else:
                from django.contrib.auth.models import AnonymousUser

                request.user, request.auth = AnonymousUser(), None

        def check_permissions(self, request):
            """
            Check if the request should be permitted.
            Raises an appropriate exception if the request is not permitted.
            """
            for permission in self.get_permissions():
                if not permission.has_permission(request, self):
                    self.permission_denied(
                        request, message=getattr(permission, 'message', None)
                    )

        def initialize_request(self, request, *args, **kwargs):
            """
            Returns the initial request object.
            """
            return request

        def initial(self, request, *args, **kwargs):
            """
            Runs anything that needs to occur prior to calling the method
            handler.
            """
            # Ensure that the incoming request is permitted
            self.perform_authentication(request)
            self.check_permissions(request)

        def finalize_response(self, request, response, *args, **kwargs):
            """
            Returns the final response object.
            """
            return response

        def handle_exception(self, exc):
            """
            Handle any exception that occurs, by returning an appropriate
            response, or re-raising the error.
            """
            raise exc

        def dispatch(self, request, *args, **kwargs):
            """
            `.dispatch()` is pretty much the same as Django's regular
            dispatch, but with extra hooks for startup, finalize, and
            exception handling.
            """
            self.args = args
            self.kwargs = kwargs
            request = self.initialize_request(request, *args, **kwargs)
            self.request = request

            try:
                self.initial(request, *args, **kwargs)
                response = super().dispatch(request, *args, **kwargs)
            except Exception as exc:
                response = self.handle_exception(exc)

            self.response = self.finalize_response(request, response, *args,
                                                   **kwargs)
            return self.response

        def setup(self, request, *args, **kwargs):
            """Initialize attributes shared by all view methods."""
            self.request = request
            self.args = args
            self.kwargs = kwargs
