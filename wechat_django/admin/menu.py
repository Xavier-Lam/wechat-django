from urllib.parse import parse_qsl

from django import forms
from django.contrib import admin
from django.db import models as m
from django.utils.translation import ugettext as _

from ..models import Menu
from .bases import DynamicChoiceForm, WechatAdmin

class MenuAdmin(WechatAdmin):
    fields = ("name", "menuid", "type", "key", "url", "appid", "pagepath",
        "weight", "created", "updated")

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

admin.site.register(Menu, MenuAdmin)