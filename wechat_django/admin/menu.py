from urllib.parse import parse_qsl

from django.contrib import admin
from django.db import models as m
# import mptt
# from mptt.admin import MPTTModelAdmin
# from mptt.models import TreeForeignKey

from ..models import Menu
from .bases import WechatAdmin

# TreeForeignKey(
#     Menu, 
#     on_delete=m.CASCADE, null=True, blank=True
# ).contribute_to_class(Menu, "parent")
# mptt.register(Menu, order_insertion_by=["-weight"])

class MenuAdmin(WechatAdmin):
    fields = ("name", "menuid", "type", "weight", "created", "updated")

    def changelist_view(self, request, *args, **kwargs):
        self.app_id = kwargs.pop("app_id", None)
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

admin.site.register(Menu, MenuAdmin)