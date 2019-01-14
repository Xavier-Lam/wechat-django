from urllib.parse import parse_qsl

from django import forms
from django.contrib import admin
from django.utils.translation import ugettext as _

from ..models import (EventType, MessageHandler, ReceiveMsgType, 
    Reply, ReplyMsgType, Rule)
from ..utils import check_wechat_permission, enum2choices

class RuleInline(admin.StackedInline):
    model = Rule
    extra = 0
    min_num = 1

    class RuleForm(forms.ModelForm):
        msg_type = forms.ChoiceField(label=_("message type"), 
            choices=enum2choices(ReceiveMsgType), required=False)
        event = forms.ChoiceField(label=_("event"), 
            choices=enum2choices(EventType), required=False)
        key = forms.CharField(label=_("event key"), required=False)
        content = forms.CharField(label=_("value"), required=False)

        class Meta(object):
            model = Rule
            fields = ("type", "weight")

        def __init__(self, *args, **kwargs):
            inst = kwargs.get("instance")
            if inst:
                type = inst.type
                initial = kwargs.get("initial", {})
                if type in (Rule.Type.CONTAIN, Rule.Type.REGEX, Rule.Type.EQUAL):
                    initial["content"] = inst.rule
                elif type == Rule.Type.MSGTYPE:
                    initial["msg_type"] = inst.rule
                elif type == Rule.Type.EVENT:
                    initial["event"] = inst.rule
                elif type == Rule.Type.EVENTKEY:
                    initial["event"] = inst.rule["event"]
                    initial["content"] = inst.rule["key"]
                kwargs["initial"] = initial
            super().__init__(*args, **kwargs)

        def save(self, commit=True, *args, **kwargs):
            model = super().save(False, *args, **kwargs)
            type = self.cleaned_data["type"]
            if type in (Rule.Type.CONTAIN, Rule.Type.REGEX, Rule.Type.EQUAL):
                model.rule = self.cleaned_data["content"]
            elif type == Rule.Type.MSGTYPE:
                model.rule = self.cleaned_data["msg_type"]
            elif type == Rule.Type.EVENT:
                model.rule = self.cleaned_data["event"]
            elif type == Rule.Type.EVENTKEY:
                model.rule = dict()
                model.rule["event"] = self.cleaned_data["event"]
                model.rule["key"] = self.cleaned_data["content"]
            if commit:
                model.save()
            return model
    form = RuleForm


class ReplyInline(admin.StackedInline):
    model = Reply
    extra = 0

    class ReplyForm(forms.ModelForm):
        program = forms.CharField(label=_("program"))
        url = forms.URLField(label=_("url"))
        content = forms.CharField(label=_("content"))

        class Meta(object):
            model = Reply
            fields = ("msg_type", )
    form = ReplyForm

class MessageHandlerAdmin(admin.ModelAdmin):
    inlines = (RuleInline, ReplyInline)
    list_filter = ("app", )

    fields = ("name", "strategy", "starts", "ends", "available",
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