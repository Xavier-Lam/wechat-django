# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from wechatpy.exceptions import WeChatException

from ..models import Menu, WeChatApp
from .bases import DynamicChoiceForm, register_admin, WeChatAdmin


@register_admin(Menu)
class MenuAdmin(WeChatAdmin):
    __category__ = "menu"

    actions = ("sync", "publish")

    list_display = (
        "operates", "id", "parent_id", "title", "type", "detail", "weight",
        "updated_at")
    list_display_links = ("title",)
    list_editable = ("weight", )
    fields = (
        "name", "type", "key", "url", "appid", "pagepath", "created_at",
        "updated_at")

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

    def operates(self, obj):
        query = dict(
            _changelist_filters=urlencode(dict(
                app_id=obj.app_id
            ))
        )
        del_link = reverse("admin:wechat_django_menu_delete", args=(obj.id,))
        del_url = "{0}?{1}".format(del_link, urlencode(query))
        rv = '<a class="deletelink" href="{0}"></a>'.format(del_url)
        if not obj.parent and not obj.type and obj.sub_button.count() < 5:
            query["parent_id"] = obj.id
            add_link = reverse("admin:wechat_django_menu_add")
            add_url = "{0}?{1}".format(add_link, urlencode(query))
            rv += '<a class="addlink" href="{0}"></a>'.format(add_url)
        return rv
    operates.short_description = _("actions")
    operates.allow_tags = True

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

    def publish(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            Menu.publish(app)
            self.message_user(request, "menus successfully published")
        except Exception as e:
            msg = "publish failed with {0}".format(e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    publish.short_description = _("publish")

    def get_actions(self, request):
        actions = super(MenuAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_fields(self, request, obj=None):
        fields = list(super(MenuAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("created_at")
            fields.remove("updated_at")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(MenuAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("created_at", "updated_at")
        return rv

    def get_queryset(self, request):
        rv = super(MenuAdmin, self).get_queryset(request)
        if not self._get_request_params(request, "menuid"):
            rv = rv.filter(menuid__isnull=True)
        if request.GET.get("parent_id"):
            rv = rv.filter(parent_id=request.GET["parent_id"])
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

    def save_model(self, request, obj, form, change):
        if not change and request.GET.get("parent_id"):
            obj.parent_id = request.GET["parent_id"]
        return super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        if not super(MenuAdmin, self).has_add_permission(request):
            return False
        # 判断菜单是否已满
        q = self.get_queryset(request)
        if request.GET.get("parent_id"):
            return q.count() < 5
        else:
            return q.filter(parent_id__isnull=True).count() < 3
