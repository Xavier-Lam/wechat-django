try:
    from rest_framework.exceptions import NotAuthenticated, PermissionDenied
except ImportError:
    from django.utils.translation import gettext_lazy as _

    class APIException(Exception):
        """
        Base class for REST framework exceptions.
        Subclasses should provide `.status_code` and `.default_detail`
        properties.
        """
        status_code = 500
        default_detail = _('A server error occurred.')
        default_code = 'error'

        def __init__(self, detail=None, code=None):
            if detail is None:
                detail = self.default_detail
            if code is None:
                code = self.default_code

        def __str__(self):
            return str(self.detail)

        def get_codes(self):
            return self.default_code

        def get_full_details(self):
            return self.default_detail

    class NotAuthenticated(APIException):
        status_code = 401
        default_detail = _('Authentication credentials were not provided.')
        default_code = 'not_authenticated'

    class PermissionDenied(APIException):
        status_code = 403
        default_detail = _('You do not have permission to perform this '
                           'action.')
        default_code = 'permission_denied'
