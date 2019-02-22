# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatException

from ..models import MessageHandler, Reply, Rule, WeChatApp
from ..utils.admin import enum2choices
from .bases import DynamicChoiceForm, register_admin, WeChatAdmin


class RuleInline(admin.StackedInline):
    model = Rule
    extra = 0
    min_num = 1

    class RuleForm(DynamicChoiceForm):
        origin_fields = ("type", "weight")

        msg_type = forms.ChoiceField(label=_("message type"),
            choices=enum2choices(Rule.ReceiveMsgType), required=False)
        event = forms.ChoiceField(label=_("event"),
            choices=enum2choices(MessageHandler.EventType), required=False)
        key = forms.CharField(label=_("event key"), required=False)
        pattern = forms.CharField(label=_("pattern"), required=False)
        # media_id = forms.CharField(label=_("media_id"), required=False)

        class Meta(object):
            model = Rule
            fields = ("type", "weight")

        def allowed_fields(self, type, cleaned_data):
            if type in (Rule.Type.CONTAIN, Rule.Type.REGEX, Rule.Type.EQUAL):
                fields = ("pattern", )
            elif type == Rule.Type.EVENT:
                fields = ("event", )
            elif type == Rule.Type.EVENTKEY:
                fields = ("event", "key")
            elif type == Rule.Type.MSGTYPE:
                fields = ("msg_type", )
            else:
                fields = tuple()
            return fields
    form = RuleForm


class ReplyInline(admin.StackedInline):
    model = Reply
    extra = 0

    class ReplyForm(DynamicChoiceForm):
        origin_fields = ("type",)

        program = forms.CharField(label=_("custom program"), required=False)
        url = forms.URLField(label=_("url"), required=False)
        content = forms.CharField(label=_("content"), widget=forms.Textarea,
            required=False)
        media_id = forms.CharField(label=_("media_id"), required=False)
        title = forms.CharField(label=_("title"), required=False)
        description = forms.CharField(label=_("description"),
            widget=forms.Textarea, required=False)
        music_url = forms.URLField(label=_("url"), required=False)
        hq_music_url = forms.URLField(label=_("HQ music url"), required=False)
        thumb_media_id = forms.CharField(label=_("thumb media_id"),
            required=False)

        class Meta(object):
            model = Reply
            fields = ("type", )

        def allowed_fields(self, type, cleaned_data):
            if type == Reply.MsgType.FORWARD:
                fields = ("url", )
            elif type == Reply.MsgType.CUSTOM:
                fields = ("program", )
            elif type == Reply.MsgType.NEWS:
                fields = ("media_id", )
            elif type in (Reply.MsgType.VOICE, Reply.MsgType.IMAGE):
                fields = ("media_id", )
            elif type == Reply.MsgType.VIDEO:
                fields = ("media_id", "title", "description")
            elif type == Reply.MsgType.MUSIC:
                fields = ("title", "description", "music_url", "hq_music_url",
                    "thumb_media_id")
            elif type == Reply.MsgType.TEXT:
                fields = ("content", )
            return fields

        # TODO: 表单验证
    form = ReplyForm


@register_admin(MessageHandler)
class MessageHandlerAdmin(WeChatAdmin):
    __category__ = "messagehandler"

    class AvailableFilter(admin.SimpleListFilter):
        title = _("available")
        parameter_name = "available"

        def lookups(self, request, model_admin):
            return [(True, _("available"))]

        def queryset(self, request, queryset):
            if self.value():
                now = timezone.now()
                queryset = (queryset.filter(enabled=True)
                    .exclude(starts__gt=now).exclude(ends__lte=now))
            return queryset

    actions = ("sync", )
    list_display = (
        "name", "is_sync", "available", "enabled", "weight", "starts", "ends",
        "updated_at", "created_at")
    list_editable = ("weight",)
    list_filter = (AvailableFilter, )
    search_fields = ("name", "rules__content", "replies__content")

    inlines = (RuleInline, ReplyInline)
    fields = ("name", "strategy", "starts", "ends", "enabled", "log",
        "weight", "created_at", "updated_at")

    def sync(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            handlers = MessageHandler.sync(app)
            msg = _("%(count)d handlers successfully synchronized")
            self.message_user(request, msg % dict(count=len(handlers)))
        except Exception as e:
            msg = _("sync failed with %(exc)s") % dict(exc=e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("sync")

    def is_sync(self, obj):
        return obj.src in (MessageHandler.Source.MP, MessageHandler.Source.MENU)
    is_sync.boolean = True
    is_sync.short_description = _("synchronized from wechat")

    def changelist_view(self, request, extra_context=None):
        post = request.POST.copy()
        if admin.helpers.ACTION_CHECKBOX_NAME not in post:
            post.update({admin.helpers.ACTION_CHECKBOX_NAME: None})
            request._set_post(post)
        return super(MessageHandlerAdmin, self).changelist_view(
            request, extra_context)

    def get_fields(self, request, obj=None):
        fields = list(super(MessageHandlerAdmin, self).get_fields(request, obj))
        if not obj:
            fields.remove("created_at")
            fields.remove("updated_at")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super(MessageHandlerAdmin, self).get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("created_at", "updated_at")
        return rv

    def save_model(self, request, obj, form, change):
        obj.src = MessageHandler.Source.SELF
        return super(MessageHandlerAdmin, self).save_model(
            request, obj, form, change)
