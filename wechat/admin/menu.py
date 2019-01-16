from urllib.parse import parse_qsl

from django.contrib import admin
from django.db import models as m
# import mptt
# from mptt.admin import MPTTModelAdmin
# from mptt.models import TreeForeignKey

from ..models import Menu

# TreeForeignKey(
#     Menu, 
#     on_delete=m.CASCADE, null=True, blank=True
# ).contribute_to_class(Menu, "parent")
# mptt.register(Menu, order_insertion_by=["-weight"])

class MenuAdmin(admin.ModelAdmin):
    list_filter = ("app", )
    fields = ("name", "menuid", "parent", "type", "weight", "created", "updated")

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if not obj:
            fields.remove("created")
            fields.remove("updated")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super().get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("created", "updated")
        return rv

    def get_queryset(self, request):
        rv = super().get_queryset(request)
        try:
            id = request.GET.get("app__id__exact")
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
            query = request.GET.get("_changelist_filters")
            if query:
                query = dict(parse_qsl(query))
                return query.get("app__id__exact")
        except:
            return None

admin.site.register(Menu, MenuAdmin)