class BasePermission(object):
    def has_permission(self, request, view):
        raise NotImplementedError

    def has_object_permission(self, request, view, obj):
        return self.has_permission(request, view)
