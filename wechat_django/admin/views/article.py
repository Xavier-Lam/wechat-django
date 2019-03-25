# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin, messages
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
import object_tool
from wechatpy.exceptions import WeChatClientException

from ...models import Article
from ..utils import anchor
from ..base import WeChatModelAdmin


class ArticleAdmin(WeChatModelAdmin):
    __category__ = "article"
    __model__ = Article

    changelist_object_tools = ("sync",)
    list_display = ("title", "author", "material_link", "index", "digest",
        "link", "source_url", "synced_at")
    list_editable = ("index",)
    search_fields = ("title", "author", "digest", "content_source_url", "content")

    fields = ("title", "author", "digest", "thumb_image", "thumb_media_id",
        "link", "show_cover_pic", "_content", "content_source_url", "source_url")
    readonly_fields = fields

    link = anchor(_("link"), lambda self, obj: obj.url)
    link.short_description = _("link")

    source_url = anchor(_("source_url"),
        lambda self, obj: obj.content_source_url)
    source_url.short_description = _("source_url")

    @mark_safe
    def thumb_image(self, obj):
        return obj.thumb_url and '<a href="{0}"><img width="200" src="{0}" /></a>'.format(obj.thumb_url)
    thumb_image.short_description = _("thumb_url")

    @mark_safe
    def material_link(self, obj):
        m = obj.material
        if m:
            return '<a href="{link}" title="{title}">{title}</a>'.format(
                link=reverse(
                    "admin:wechat_django_material_change",
                    kwargs=dict(
                        object_id=m.id,
                        wechat_app_id=m.app_id
                    )
                ),
                title="{comment} ({media_id})".format(
                    comment=m.comment,
                    media_id=m.media_id
                ) if m.comment else m.media_id
            )
    material_link.short_description = _("material")

    @mark_safe
    def _content(self, obj):
        return obj.content
    _content.short_description = _("content")

    def get_queryset(self, request):
        base_q = super(WeChatModelAdmin, self).get_queryset(request)
        return base_q.filter(material__app_id=request.app_id)

    def get_actions(self, request):
        actions = super(ArticleAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    @object_tool.confirm(short_descrition=_("Sync articles"))
    def sync(self, request, obj=None):
        self.check_wechat_permission(request, "sync")
        def action():
            materials = Article.sync(request.app)
            msg = _("%(count)d articles successfully synchronized")
            return msg % dict(count=len(materials))
        
        return self._clientaction(
            request, action, _("Sync articles failed with %(exc)s"))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
