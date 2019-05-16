# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import object_tool

from ...models import Template
from ..base import WeChatModelAdmin


class TemplateAdmin(WeChatModelAdmin):
    __category__ = "template"
    __model__ = Template

    actions = None
    changelist_object_tools = ("sync",)
    list_display = ("template_id", "title", "content", "created_at")
    search_fields = (
        "template_id", "title", "content", "primary_industry",
        "deputy_industry", "comment")

    fields = (
        "template_id", "title", "content", "primary_industry",
        "deputy_industry", "example", "comment", "created_at")
    readonly_fields = (
        "template_id", "title", "content", "primary_industry",
        "deputy_industry", "example", "created_at")

    @object_tool.confirm(short_description=_("Sync templates"))
    def sync(self, request, obj=None):
        self.check_wechat_permission(request, "sync")

        def action():
            templates = Template.sync(request.app)
            msg = _("%(count)d templates successfully synchronized")
            return msg % dict(count=len(templates))

        return self._clientaction(
            request, action, _("Sync templates failed with %(exc)s"))
    sync.short_description = _("sync templates")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
