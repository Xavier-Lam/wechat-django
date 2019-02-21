# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatException

from ..models import Material
from .bases import DynamicChoiceForm, register_admin, WeChatAdmin


@register_admin(Material)
class MaterialAdmin(WeChatAdmin):
    __category__ = "material"

    actions = ("delete_selected", "sync", )
    list_display = ("media_id", "type", "comment", "updatetime")
    list_filter = ("type", )
    search_fields = ("name", "media_id", "comment")

    fields = ("type", "media_id", "name", "open", "comment")
    readonly_fields = ("type", "media_id", "name", "open", "media_id")

    @mark_safe
    def preview(self, obj):
        if obj.type == Material.Type.IMAGE:
            return u'<img src="%s" />'%obj.url
    preview.short_description = _("preview")
    preview.allow_tags = True

    def updatetime(self, obj):
        return timezone.datetime.fromtimestamp(obj.update_time)
    updatetime.short_description = _("update time")

    @mark_safe
    def open(self, obj):
        blank = True
        request = self.request
        if obj.type == Material.Type.NEWS:
            url = "{0}?{1}".format(
                reverse("admin:wechat_django_article_changelist"),
                urlencode(dict(
                    app_id=self.get_app(request).id,
                    material_id=obj.id
                ))
            )
            blank = False
        elif obj.type == Material.Type.VOICE:
            # 代理下载
            app = self.get_app(request)
            url = reverse("wechat_django:material_proxy", kwargs=dict(
                appname=app.name,
                media_id=obj.media_id
            ))
        else:
            url = obj.url
        return '<a href="{0}" {1}>{2}</a>'.format(
            url, 'target="_blank"' if blank else "", _("open")
        )
    open.short_description = _("open")
    open.allow_tags = True

    def sync(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            materials = Material.sync(app)
            msg = "%(count)d materials successfully synchronized"
            self.message_user(request, msg % dict(count=len(materials)))
        except Exception as e:
            msg = "sync failed with %(exc)s" % dict(exc=e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("sync")

    def delete_selected(self, request, obj):
        for o in obj.all():
            try:
                o.delete()
            except WeChatException:
                msg = _("delete material failed: %(obj)s") % dict(obj=obj)
                self.logger(request).warning(msg, exc_info=True)
                raise
    delete_selected.short_description = _("delete selected")

    def has_add_permission(self, request):
        return False
