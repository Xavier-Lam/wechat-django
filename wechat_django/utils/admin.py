from django.http.response import HttpResponseRedirect
from object_tool.shortcuts import OBJECTTOOL_ALLOWED_PROPERTIES


def link(url, short_description, **kwargs):
    """
    A short cut for superlink object tool

        class DebugAdmin(CustomObjectToolModelAdminMixin, ModelAdmin):
            object_tools = ["forkme"]

            forkme = link(
                "https://github.com/Xavier-Lam/django-object-tool", _("fork"))
    """
    def wrapper(modeladmin, request, obj=None):
        nonlocal url
        if callable(url):
            url = url(modeladmin, request, obj)
        return HttpResponseRedirect(url)

    kwargs["short_description"] = short_description
    kwargs["allow_get"] = True
    kwargs["href"] = url
    for key, value in kwargs.items():
        if key in OBJECTTOOL_ALLOWED_PROPERTIES:
            setattr(wrapper, key, value)

    return wrapper
