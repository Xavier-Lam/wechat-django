# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from ..models import MessageLog
from ..utils.admin import linkify
from .base import WeChatModelAdmin


class MessageLogAdmin(WeChatModelAdmin):
    __category__ = "messagelog"
    __model__ = MessageLog

    list_display = (
        "msg_id", linkify("user"), "type", "content", "created_at")
    list_filter = ("type", )
    search_fields = (
        "=user__openid", "=user__unionid", "user__nickname", "user__comment",
        "content")

    fields = (
        "msg_id", linkify("user"), "type", "content", "created_at")
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
