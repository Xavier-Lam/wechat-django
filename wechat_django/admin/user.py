from django import forms
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.translation import ugettext as _

from ..models import WeChatApp, WeChatUser
from .bases import DynamicChoiceForm, WeChatAdmin

class WeChatUserAdmin(WeChatAdmin):
    actions = ("sync", "sync_all", "update")
    list_display = ("openid", "nickname", "avatar", "subscribe", "remark",# "groupid", 
        "created")
    search_fields = ("=openid", "=unionid", "nickname", "remark")
    
    fields = ("avatar", "nickname", "openid", "unionid", "sex",
        "city", "province", "country", "language", "subscribe",
        "subscribetime", "subscribe_scene", "qr_scene", "qr_scene_str", 
        "remark", "comment", "groupid", "created", "updated")
    
    def avatar(self, obj):
        return u'<img src="%s" />'%obj.avatar(46)
    avatar.short_description = _("avatar")
    avatar.allow_tags = True

    def subscribetime(self, obj):
        return obj.subscribe_time and timezone.datetime.fromtimestamp(obj.subscribe_time)
    subscribetime.short_description = "subscribe time"
    
    def sync(self, request, queryset, method="sync", kwargs=None):
        # 可能抛出48001 没有api权限
        kwargs = kwargs or dict()
        app_id = self.get_request_app_id(request)
        app = WeChatApp.get_by_id(app_id)
        try:
            users = getattr(WeChatUser, method)(app, **kwargs)
            self.message_user(request, 
                "%d users successfully synchronized"%len(users))
        except Exception as e:
            self.message_user(request, 
                method + " failed with %s"%str(e), level=messages.ERROR)
    sync.short_description = _("sync")
    sync_all = lambda self, request, queryset: self.sync(
        request, queryset, kwargs=dict(all=True))
    sync_all.short_description = _("sync all")
    update = lambda self, request, queryset: self.sync(
        request, queryset, "fetch_users", dict(
            openids=[o.openid for o in queryset.all()]
        ))
    update.short_description = _("update selected")

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_readonly_fields(self, request, obj=None):
        return tuple(o for o in self.fields if o not in ("remark", "comment"))

    def save_model(self, request, obj, form, change):
        if "remark" in form.changed_data:
            obj.app.client.user.update_remark(obj.openid, obj.remark)
        return super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(WeChatUser, WeChatUserAdmin)