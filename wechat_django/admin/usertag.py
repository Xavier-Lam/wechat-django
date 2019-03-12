# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatException

from ..models import UserTag
from .bases import register_admin, WeChatAdmin


@register_admin(UserTag)
class UserTagAdmin(WeChatAdmin):
    __category__ = "usertag"

    actions = ("sync", )
    list_display = ("id",  "name", "sys_tag", "count", "created_at")
    search_fields = ("name", )

    fields = list_display
    readonly_fields = ("id", "count", "sys_tag")

    def sync(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            tags = UserTag.sync(app)
            msg = _("%(count)d tags successfully synchronized")
            self.message_user(request, msg % dict(count=len(tags)))
        except Exception as e:
            msg = _("sync failed with %(exc)s") % dict(exc=e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("sync tags")

    @mark_safe
    def count(self, obj):
        return obj.users.count()
    count.short_description = _("users count")
    count.allow_tags = True

    def get_fields(self, request, obj=None):
        fields = list(super(UserTagAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("created_at",)
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(UserTagAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("created_at",)
        return rv

    def has_delete_permission(self, request, obj=None):
        rv = super(UserTagAdmin, self).has_delete_permission(request, obj)
        if rv and obj:
            return not obj.sys_tag()
        return rv

    def has_add_permission(self, request):
        return super(UserTagAdmin, self).has_add_permission(request)\
            and self.get_queryset(request).exclude(
                id__in=UserTag.SYS_TAGS).count() < 100
