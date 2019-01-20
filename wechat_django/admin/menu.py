from django import forms
from django.contrib import admin, messages
from django.db import models as m
from django.utils.translation import ugettext as _

from ..models import Menu, WechatApp
from .bases import DynamicChoiceForm, WechatAdmin

class MenuAdmin(WechatAdmin):
    # change_form_template = "admin/wechat_django/menu/change_form.html"
    actions = ("sync", )

    fields = ("name", "menuid", "type", "key", "url", "appid", "pagepath",
        "weight", "created", "updated")

    def sync(self, request, queryset):
        app_id = self.get_request_app_id(request)
        app = WechatApp.get_by_id(app_id)
        try:
            Menu.sync(app)
            self.message_user(request, "menus successfully synchronized")
        except Exception as e:
            raise
            self.message_user(request, 
                "sync failed with %s"%str(e), level=messages.ERROR)
    sync.short_description = _("sync")

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

    class MenuForm(DynamicChoiceForm):
        content_field = "content"
        origin_fields = ("name", "menuid", "type", "weight")
        type_field = "type"

        key = forms.CharField(label=_("menu key"), required=False)
        url = forms.URLField(label=_("url"), required=False)
        appid = forms.CharField(label=_("app_id"), required=False)
        pagepath = forms.CharField(label=_("pagepath"), required=False)
        
        class Meta(object):
            model = Menu
            fields = ("name", "menuid", "type", "weight")
            
        def allowed_fields(self, type, cleaned_data):
            if type == Menu.Event.VIEW:
                fields = ("url", )
            elif type == Menu.Event.CLICK:
                fields = ("key", )
            elif type == Menu.Event.MINIPROGRAM:
                fields = ("url", "appid", "apppath")
            else:
                fields = tuple()
            return fields
    form = MenuForm

    def has_add_permission(self, request):
        return (super().has_add_permission(request) 
            and self.get_queryset(request).count() < 3)

admin.site.register(Menu, MenuAdmin)