from urllib.parse import parse_qsl

from django.contrib import admin
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

class WechatAppListFilter(admin.SimpleListFilter):
    title = _("wechat app")

    parameter_name = "app_id"

    def lookups(self, request, model_admin):
        # 过滤有权限的appid
        from ..models import WechatApp # TODO: 引入路径
        return tuple(
            (app.id, app.name)
            for app in WechatApp.objects.all()
        )

    def queryset(self, request, queryset):
        return queryset.filter(app_id=self.value())

    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == force_text(lookup),
                'query_string': changelist.get_query_string({self.parameter_name: lookup}, []),
                'display': title,
            }

class WechatAdmin(admin.ModelAdmin):
    # list_filter = (WechatAppListFilter, )
    app_id = None
    change_form_template = "admin/wechat_django/wechat_admin/change_form.html"
    change_list_template = "admin/wechat_django/wechat_admin/change_list.html"

    def changelist_view(self, request, *args, **kwargs):
        self.app_id = kwargs.pop("app_id", None)
        kwargs["extra_context"] = kwargs.get("extra_context", {})
        kwargs["extra_context"]["app_id"] = self.get_request_app_id(request)
        return super().changelist_view(request, *args, **kwargs)
    def add_view(self, request, *args, **kwargs):
        self.app_id = kwargs.pop("app_id", None)
        return super().add_view(request, *args, **kwargs)
    def history_view(self, request, *args, **kwargs):
        self.app_id = kwargs.pop("app_id", None)
        return super().history_view(request, *args, **kwargs)
    def delete_view(self, request, *args, **kwargs):
        self.app_id = kwargs.pop("app_id", None)
        return super().delete_view(request, *args, **kwargs)
    def change_view(self, request, *args, **kwargs):
        self.app_id = kwargs.pop("app_id", None)
        return super().change_view(request, *args, **kwargs)
    def render_change_form(self, request, context, *args, **kwargs):
        context["app_id"] = self.get_request_app_id(request)
        return super().render_change_form(request, context, *args, **kwargs)

    def get_queryset(self, request):
        rv = super().get_queryset(request)
        id = self.get_request_app_id(request)
        if not id:
            rv = rv.none()
        # TODO: 检查权限
        return rv
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = self.get_request_app_id(request)
        # TODO: 没有app_id 应该404
        # TODO: 检查权限
        return super().save_model(request, obj, form, change)

    def get_model_perms(self, request):
        # 隐藏首页上的菜单
        if self.get_request_app_id(request):
            return super().get_model_perms(request)
        return {}

    def get_request_app_id(self, request):
        return self.app_id or request.resolver_match.kwargs.get("app_id")