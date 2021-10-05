from wechat_django.enums import AppType
from wechat_django.models import apps
from .base import (ApplicationTypeFilter, HostApplicationAdmin,
                   HostedApplicationAdmin, ParentApplicationFilter)


class ThirdPartyPlatformApplicationAdmin(HostApplicationAdmin):
    allowed_app_types = (AppType.THIRDPARTYPLATFORM,)
    hosted_application = apps.AuthorizerApplication

    list_display = ("__str__", "appid", "desc", "created_at", "manage")

    fields = ("title", "name", "appid", "appsecret", "token",
              "encoding_aes_key", "desc")


class AuthorizerApplicationAdmin(HostedApplicationAdmin):
    allowed_app_types = (AppType.HOSTED | AppType.MINIPROGRAM,
                         AppType.HOSTED | AppType.OFFICIALACCOUNT)
    parent_type = AppType.THIRDPARTYPLATFORM

    list_filter = (ParentApplicationFilter, ("type", ApplicationTypeFilter))

    fields = ("parent", "title", "name", "type", "appid", "desc", "pays")
