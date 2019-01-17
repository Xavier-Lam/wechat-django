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

class WechatAdminMixin(object):
    list_filter = (WechatAppListFilter, )

    def get_queryset(self, request):
        rv = super().get_queryset(request)
        try:
            id = request.GET.get("app_id")
            if not id:
                id = self._get_appid(request)
                if not id:
                    rv = rv.none()
        except:
            rv = rv.none()
        # TODO: 检查权限
        return rv
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = self._get_appid(request)
        # TODO: 检查权限
        return super().save_model(request, obj, form, change)

    def _get_appid(self, request):
        try:
            query = self.get_preserved_filters(request)
            query = dict(parse_qsl(query))
            if query.get("_changelist_filters"):
                return dict(parse_qsl(query["_changelist_filters"])).get("app_id")
        except:
            return None

    # def response_add(self, request)