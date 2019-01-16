from urllib.parse import parse_qsl

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext as _

from ..models import (EventType, MessageHandler, ReceiveMsgType, 
    Reply, ReplyMsgType, Rule)
from ..utils import check_wechat_permission, enum2choices

class MessageHandlerForm(forms.ModelForm):
    content_field = ""
    type_field = ""
    origin_fields = tuple()

    def __init__(self, *args, **kwargs):
        inst = kwargs.get("instance")
        if inst:
            type = getattr(inst, self.type_field)
            initial = kwargs.get("initial", {})
            initial.update(getattr(inst, self.content_field))
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        type = cleaned_data[self.type_field]
        fields = self.allowed_fields(type, cleaned_data)
        
        content = dict()
        for k in set(cleaned_data.keys()).difference(self.origin_fields):
            if k in fields:
                content[k] = cleaned_data[k]
            del cleaned_data[k]
        cleaned_data[self.content_field] = content
        return cleaned_data

    def allowed_fields(self, type, cleaned_data):
        raise NotImplementedError()

    def save(self, commit=True, *args, **kwargs):
        model = super().save(False, *args, **kwargs)
        setattr(model, self.content_field, 
            self.cleaned_data[self.content_field])
        if commit:
            model.save()
        return model

class RuleInline(admin.StackedInline):
    model = Rule
    extra = 0
    min_num = 1

    class RuleForm(MessageHandlerForm):
        content_field = "rule"
        origin_fields = ("type", "weight")
        type_field = "type"

        msg_type = forms.ChoiceField(label=_("message type"), 
            choices=enum2choices(ReceiveMsgType), required=False)
        event = forms.ChoiceField(label=_("event"), 
            choices=enum2choices(EventType), required=False)
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

    class ReplyForm(MessageHandlerForm):
        content_field = "content"
        origin_fields = ("msg_type",)
        type_field = "msg_type"

        program = forms.CharField(label=_("program"), required=False)
        url = forms.URLField(label=_("url"), required=False)
        content = forms.CharField(label=_("content"), required=False)
        media_id = forms.CharField(label=_("media_id"), required=False)

        class Meta(object):
            model = Reply
            fields = ("msg_type", )
        
        def allowed_fields(self, type, cleaned_data):
            if type == ReplyMsgType.FORWARD:
                fields = ("url", )
            elif type == ReplyMsgType.CUSTOM:
                fields = ("program", )
            elif type == ReplyMsgType.NEWS:
                fields = ("content", "media_id")
            elif type in (ReplyMsgType.MUSIC, ReplyMsgType.VIDEO, 
                ReplyMsgType.VOICE, ReplyMsgType.IMAGE):
                fields = ("media_id", )
            elif type == ReplyMsgType.TEXT:
                fields = ("content", )
            return fields
    form = ReplyForm

class MessageHandlerAdmin(admin.ModelAdmin):
    inlines = (RuleInline, ReplyInline)
    list_display = ("name", "available", "enabled", "starts", "ends")
    list_filter = ("app", )

    fields = ("name", "strategy", "starts", "ends", "enabled",
        "weight", "created", "updated")

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if not obj:
            fields.remove("created")
            fields.remove("updated")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super().get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("created", "updated")
        return rv

    def get_queryset(self, request):
        rv = super().get_queryset(request)
        try:
            id = request.GET.get("app__id__exact")
            if not id:
                id = self._get_appid(request)
                if not id:
                    rv = rv.none()
        except:
            rv = rv.none()
        # TODO: 检查权限
        return rv
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = self._get_appid(request)
        # TODO: 检查权限
        return super().save_model(request, obj, form, change)

    def _get_appid(self, request):
        try:
            query = request.GET.get("_changelist_filters")
            if query:
                query = dict(parse_qsl(query))
                return query.get("app__id__exact")
        except:
            return None

admin.site.register(MessageHandler, MessageHandlerAdmin)