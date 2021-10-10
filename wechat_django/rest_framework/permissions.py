try:
    from rest_framework.permissions import BasePermission, IsAuthenticated
except ImportError:
    class BasePermission:
        def has_permission(self, request, view):
            raise NotImplementedError

        def has_object_permission(self, request, view, obj):
            return self.has_permission(request, view)

    class IsAuthenticated(BasePermission):
        def has_permission(self, request, view):
            return bool(request.user and request.user.is_authenticated)
