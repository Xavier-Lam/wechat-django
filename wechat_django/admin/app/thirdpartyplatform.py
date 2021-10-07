from django.utils.translation import ugettext_lazy as _

from wechat_django.enums import AppType
from wechat_django.models import apps
from .base import (ApplicationTypeFilter, HostApplicationAdmin,
                   HostedApplicationAdmin, ParentApplicationFilter)


class ThirdPartyPlatformApplicationAdmin(HostApplicationAdmin):
    allowed_app_types = (AppType.THIRDPARTYPLATFORM,)
    hosted_application = apps.AuthorizerApplication

    list_display = ("__str__", "appid", "desc", "created_at", "manage")

    fields = ("title", "name", "appid", "appsecret", "token",
              "encoding_aes_key", "desc", "notify_url",
              "authorizer_notify_url")

    def authorizer_notify_url(self, obj):
        return obj and obj.authorizer_notify_url(self.request)
    authorizer_notify_url.short_description = _("Authorizer message notify "
                                                "URL")

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj=obj)
        if not obj:
            return tuple(field for field in fields if field not in
                         ("authorizer_notify_url",))
        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields + ("authorizer_notify_url",)


class AuthorizerApplicationAdmin(HostedApplicationAdmin):
    allowed_app_types = (AppType.HOSTED | AppType.MINIPROGRAM,
                         AppType.HOSTED | AppType.OFFICIALACCOUNT)
    parent_type = AppType.THIRDPARTYPLATFORM

    list_filter = (ParentApplicationFilter, ("type", ApplicationTypeFilter))

    fields = ("parent", "title", "name", "type", "appid", "desc", "pays")
