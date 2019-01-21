from django import forms
from django.contrib import admin, messages
from django.utils.translation import ugettext as _

from ..models import WeChatApp, WeChatUser
from .bases import DynamicChoiceForm, WeChatAdmin

class WeChatUserAdmin(WeChatAdmin):
    actions = ("sync", "sync_all")
    list_display = ("openid", "nickname", "avatar", "subscribe", "remark", "groupid", 
        "created")
    
    fields = ("openid", "unionid", "nickname", "sex", "headimgurl",
        "city", "province", "country", "language", "subscribe",
        "subscribe_time", "subscribe_scene", "qr_scene", "qr_scene_str", 
        "remark", "groupid", "created", "updated")
    
    def avatar(self, obj):
        return u'<img src="%s" />'%obj.avatar(46)
    avatar.short_description = _("avatar")
    avatar.allow_tags = True
    
    def sync(self, request, queryset, kwargs=None):
        kwargs = kwargs or dict()
        app_id = self.get_request_app_id(request)
        app = WeChatApp.get_by_id(app_id)
        try:
            users = WeChatUser.sync(app, **kwargs)
            self.message_user(request, 
                "%d users successfully synchronized"%len(users))
        except Exception as e:
            self.message_user(request, 
                "sync failed with %s"%str(e), level=messages.ERROR)
    sync.short_description = _("sync")
    sync_all = lambda request, queryset: sync(request, queryset, dict(all=True))
    sync_all.short_description = _("sync all")

    def get_readonly_fields(self, request, obj=None):
        return tuple(o for o in self.fields if o != "remark")
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(WeChatUser, WeChatUserAdmin)