# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatException

from ..models import Article
from .base import register_admin, WeChatAdmin


@register_admin(Article)
class ArticleAdmin(WeChatAdmin):
    __category__ = "article"

    actions = ("sync",)
    list_display = ("title", "author", "material_link", "index", "digest",
        "link", "source_url", "synced_at")
    list_editable = ("index",)
    search_fields = ("title", "author", "digest", "content_source_url", "content")

    fields = ("title", "author", "digest", "thumb_image", "thumb_media_id",
        "link", "show_cover_pic", "_content", "content_source_url", "source_url")
    readonly_fields = fields

    @mark_safe
    def link(self, obj):
        return '<a href="{link}">{title}</a>'.format(
            link=obj.url,
            title=_("link")
        )
    link.short_description = _("link")
    link.allow_tags = True

    @mark_safe
    def source_url(self, obj):
        return obj.content_source_url and '<a href="{link}">{title}</a>'.format(
            link=obj.content_source_url,
            title=_("source_url")
        )
    source_url.short_description = _("source_url")
    source_url.allow_tags = True

    @mark_safe
    def thumb_image(self, obj):
        return obj.thumb_url and '<a href="{0}"><img width="200" src="{0}" /></a>'.format(obj.thumb_url)
    thumb_image.short_description = _("thumb_url")
    thumb_image.allow_tags = True

    @mark_safe
    def material_link(self, obj):
        m = obj.material
        if m:
            return '<a href="{link}" title="{title}">{title}</a>'.format(
                link="{path}?{query}".format(
                    path=reverse("admin:wechat_django_material_change", args=(m.id,)),
                    query=urlencode(dict(
                        app_id=self.get_app(self.request).id
                    ))
                ),
                title="{comment} ({media_id})".format(
                    comment=m.comment,
                    media_id=m.media_id
                )
            ) if m.comment else m.media_id
    material_link.short_description = _("material")
    material_link.allow_tags = True

    @mark_safe
    def _content(self, obj):
        return obj.content
    _content.short_description = _("content")
    _content.allow_tags = True

    def _filter_app_id(self, queryset, app_id):
        return queryset.filter(material__app_id=app_id)

    def get_actions(self, request):
        actions = super(ArticleAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def sync(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            materials = Article.sync(app)
            msg = _("%(count)d articles successfully synchronized")
            self.message_user(request, msg % dict(count=len(materials)))
        except Exception as e:
            msg = _("sync failed with %(exc)s") % dict(exc=e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("sync")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
