# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import WeChatClientException

from ..models import UserTag, WeChatUser
from .base import WeChatModelAdmin


class UserForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        UserTag.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple(_("tags"), False),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["tags"] = self.instance.tags.values_list(
                "pk", flat=True)

    def save(self, *args, **kwargs):
        instance = super(UserForm, self).save(*args, **kwargs)
        if instance.pk:
            instance.tags.set(self.cleaned_data["tags"], clear=False)
        return instance


class WeChatUserAdmin(WeChatModelAdmin):
    __category__ = "user"
    __model__ = WeChatUser

    actions = ("sync", "sync_all", "update")
    list_display = (
        "openid", "nickname", "avatar", "subscribe", "remark",  # "groupid",
        "created_at")
    search_fields = ("=openid", "=unionid", "nickname", "remark")

    fields = (
        "avatar", "nickname", "openid", "unionid", "sex", "city", "province",
        "country", "language", "subscribe", "subscribetime",
        "subscribe_scene", "qr_scene", "qr_scene_str", "remark", "comment",
        "tags", "group", "created_at", "updated_at")

    @mark_safe
    def avatar(self, obj):
        return obj.headimgurl and '<img src="{0}" />'.format(obj.avatar(46))
    avatar.short_description = _("avatar")
    avatar.allow_tags = True

    def subscribetime(self, obj):
        return obj.subscribe_time and timezone.datetime.fromtimestamp(obj.subscribe_time)
    subscribetime.short_description = _("subscribe time")

    def sync(self, request, queryset, method="sync", kwargs=None):
        self.check_wechat_permission(request, "sync")
        # 可能抛出48001 没有api权限
        kwargs = kwargs or dict()
        app = request.app
        try:
            users = getattr(WeChatUser, method)(app, **kwargs)
            msg = _("%(count)d users successfully synchronized")
            self.message_user(request, msg % dict(count=len(users)))
        except Exception as e:
            tpl = _("%(method)s failed with %(exc)s")
            msg = tpl % dict(method=_(method), exc=e)
            if isinstance(e, WeChatClientException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("incremental sync")
    sync_all = lambda self, request, queryset: self.sync(
        request, queryset, kwargs=dict(all=True))
    sync_all.short_description = _("sync all")
    update = lambda self, request, queryset: self.sync(
        request, queryset, "fetch_users", dict(
            openids=[o.openid for o in queryset.all()]
        ))
    update.short_description = _("update selected")

    def get_actions(self, request):
        actions = super(WeChatUserAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    form = UserForm

    def get_form(self, request, obj=None, **kwargs):
        # 过滤只显示自己app的标签 并过滤系统标签
        app = request.app
        form = super(WeChatUserAdmin, self).get_form(request, obj, **kwargs)
        tags_field = form.declared_fields["tags"]

        tags_field.queryset = (tags_field.queryset
            .filter(app=app)
            .exclude(id__in=UserTag.SYS_TAGS))
        return form

    def get_readonly_fields(self, request, obj=None):
        return tuple(o for o in self.fields if o not in (
            "remark", "tags", "comment"))

    def save_model(self, request, obj, form, change):
        if "remark" in form.changed_data:
            obj.app.client.user.update_remark(obj.openid, obj.remark)
        return super(WeChatUserAdmin, self).save_model(
            request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False
