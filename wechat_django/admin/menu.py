from django import forms
from django.contrib import admin, messages
from django.db import models as m
from django.utils.translation import ugettext as _
from wechatpy.exceptions import WeChatException

from ..models import Menu, WeChatApp
from .bases import DynamicChoiceForm, WeChatAdmin

class MenuAdmin(WeChatAdmin):
    __category__ = "menu"

    actions = ("sync", )

    list_display = ("title", "type", "detail", "weight", "updated")
    list_editable = ("weight", )
    fields = ("name", "type", "key", "url", "appid", "pagepath", "weight", 
        "created", "updated")

    def title(self, obj):
        if obj.parent:
            return "|--- " + obj.name
        return obj.name
    title.short_description = _("title")

    def detail(self, obj):
        if obj.type == Menu.Event.CLICK:
            return obj.content.get("key")
        elif obj.type == Menu.Event.VIEW:
            return '<a href="{0}">{1}</a>'.format(
                obj.content.get("url"), _("link"))
        elif obj.type == Menu.Event.MINIPROGRAM:
            return obj.content.get("appid")
    detail.short_description = _("detail")
    detail.allow_tags = True

    def sync(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            Menu.sync(app)
            self.message_user(request, "menus successfully synchronized")
        except Exception as e:
            msg = "sync failed with {0}".format(e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("sync")

    def get_fields(self, request, obj=None):
        fields = list(super(MenuAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("created")
            fields.remove("updated")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(MenuAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("created", "updated")
        return rv

    def get_queryset(self, request):
        rv = super(MenuAdmin, self).get_queryset(request)
        if not self._get_request_params(request, "menuid"):
            rv = rv.filter(menuid__isnull=True)
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
        return (super(MenuAdmin, self).has_add_permission(request) 
            and self.get_queryset(request).count() < 3)

admin.site.register(Menu, MenuAdmin)