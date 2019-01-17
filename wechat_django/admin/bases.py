from urllib.parse import parse_qsl

from django.contrib import admin
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

class WechatAdmin(admin.ModelAdmin):
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
        preserved_filters_str = request.GET.get('_changelist_filters')
        if preserved_filters_str:
            preserved_filters = dict(parse_qsl(preserved_filters_str))
        else:
            preserved_filters = dict()
        return (request.GET.get("app_id") 
            or preserved_filters.get("app_id") 
            or request.resolver_match.kwargs.get("app_id"))