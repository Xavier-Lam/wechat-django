from django.contrib import admin
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from object_tool import CustomObjectToolModelAdminMixin

from wechat_django.enums import AppType
from wechat_django.models import apps
from wechat_django.utils.admin import link
from .base import (ApplicationChangeList, ApplicationTypeFilter,
                   BaseApplicationAdmin)


@admin.register(apps.OrdinaryApplication)
class ApplicationAdmin(CustomObjectToolModelAdminMixin,
                       BaseApplicationAdmin):
    allowed_app_types = (AppType.UNKNOWN, AppType.WEBAPP)
    query_app_types = allowed_app_types + (AppType.MINIPROGRAM,
                                           AppType.OFFICIALACCOUNT)

    list_filter = (("type", ApplicationTypeFilter),)
    changelist_object_tools = ("create_official_application",
                               "create_miniprogram_application")

    fields = ("title", "name", "type", "appid", "appsecret",
              "access_token_url", "desc", "pays")

    create_official_application = link(
        lambda *args: reverse("admin:{0}_{1}_add".format(
            apps.OfficialAccountApplication._meta.app_label,
            apps.OfficialAccountApplication._meta.model_name)),
        _("Add an official account")
    )
    create_miniprogram_application = link(
        lambda *args: reverse("admin:{0}_{1}_add".format(
            apps.MiniProgramApplication._meta.app_label,
            apps.MiniProgramApplication._meta.model_name)),
        _("Add a miniprogram")
    )

    def get_changelist(self, request, **kwargs):
        return ApplicationChangeList


class OrdinaryApplicationAdmin(BaseApplicationAdmin):
    fields = ("title", "name", "appid", "appsecret", "token",
              "encoding_aes_key", "encrypt_strategy", "access_token_url",
              "desc", "pays", "notify_url")

    def changelist_view(self, request, extra_context=None):
        return HttpResponseRedirect(
            reverse("admin:{0}_{1}_changelist".format(
                apps.OrdinaryApplication._meta.app_label,
                apps.OrdinaryApplication._meta.model_name
            ))
        )

    def _response_post_save(self, request, obj):
        return self.changelist_view(request)

    def has_module_permission(self, request):
        return False


@admin.register(apps.OfficialAccountApplication)
class OfficialAccountApplicationAdmin(OrdinaryApplicationAdmin):
    allowed_app_types = (AppType.OFFICIALACCOUNT,)


@admin.register(apps.MiniProgramApplication)
class MiniProgramApplicationAdmin(OrdinaryApplicationAdmin):
    allowed_app_types = (AppType.MINIPROGRAM,)
