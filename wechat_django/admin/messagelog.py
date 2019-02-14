# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.db import models as m
from django.utils import timezone
from django.utils.translation import ugettext as _

from ..models import MessageLog, WeChatApp
from ..utils.admin import linkify
from .bases import WeChatAdmin


class MessageLogAdmin(WeChatAdmin):
    __category__ = "messagelog"

    list_display = ("msg_id", linkify("user"), "type", "content", "created")
    list_filter = ("type", )
    search_fields = ("=user__openid", "=user__unionid", "user__nickname",
        "user__comment", "content")

    fields = ("msg_id", linkify("user"), "type", "content",
        "create_time", "created")
    readonly_fields = fields

    def create_time(self, obj):
        return timezone.datetime.fromtimestamp(obj.createtime)
    create_time.short_description = _("create time")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(MessageLog, MessageLogAdmin)
