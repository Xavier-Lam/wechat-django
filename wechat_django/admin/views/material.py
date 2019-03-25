# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import object_tool
from wechatpy.exceptions import WeChatClientException

from ...models import Material
from ..base import (
    RecursiveDeleteActionMixin, DynamicChoiceForm, WeChatModelAdmin)


class MaterialAdmin(RecursiveDeleteActionMixin, WeChatModelAdmin):
    __category__ = "material"
    __model__ = Material

    changelist_object_tools = ("sync", )
    list_display = ("media_id", "type", "comment", "updatetime")
    list_filter = ("type", )
    search_fields = ("name", "media_id", "comment")

    fields = ("type", "media_id", "name", "open", "comment")
    readonly_fields = ("type", "media_id", "name", "open", "media_id")

    @mark_safe
    def preview(self, obj):
        if obj.type == Material.Type.IMAGE:
            return '<img src="%s" />'%obj.url
    preview.short_description = _("preview")

    def updatetime(self, obj):
        return (obj.update_time
            and timezone.datetime.fromtimestamp(obj.update_time))
    updatetime.short_description = _("update time")

    @mark_safe
    def open(self, obj):
        blank = True
        if obj.type == Material.Type.NEWS:
            url = "{0}?{1}".format(
                reverse(
                    "admin:wechat_django_article_changelist",
                    kwargs=dict(wechat_app_id=obj.app_id)
                ),
                urlencode(dict(
                    material_id=obj.id
                ))
            )
            blank = False
        elif obj.type == Material.Type.VOICE:
            # 代理下载
            app = obj.app
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

    @object_tool.confirm(short_description=_("Sync materials"))
    def sync(self, request, obj=None):
        self.check_wechat_permission(request, "sync")
        def action():
            materials = Material.sync(request.app)
            msg = _("%(count)d materials successfully synchronized")
            return msg % dict(count=len(materials))

        return self._clientaction(
            request, action, _("Sync materials failed with %(exc)s"))

    def has_add_permission(self, request):
        return False
