from django import forms
from django.contrib import admin, messages
from django.utils.translation import ugettext as _

from ..models import WeChatApp, WeChatUser
from .bases import DynamicChoiceForm, WeChatAdmin

class WeChatUserAdmin(WeChatAdmin):
    actions = ("sync", )
    
    def _sync(self, request, queryset, kwargs=None):
        kwargs = kwargs or dict()
        app_id = self.get_request_app_id(request)
        app = WeChatApp.get_by_id(app_id)
        try:
            users = WeChatUser.sync(app, **kwargs)
            self.message_user(request, 
                "%d materials successfully synchronized"%len(users))
        except Exception as e:
            self.message_user(request, 
                "sync failed with %s"%str(e), level=messages.ERROR)
    sync_all = lambda request, queryset: _sync(request, queryset, dict(all=True))
    sync_all.short_description = _("sync all")
    sync = lambda request, queryset: _sync(request, queryset)
    sync.short_description = _("sync")
    
    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

admin.site.register(WeChatUser, WeChatUserAdmin)