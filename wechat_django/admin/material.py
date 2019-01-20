from django import forms
from django.contrib import admin, messages
from django.db import models as m
from django.utils import timezone
from django.utils.translation import ugettext as _

from ..models import Material, WechatApp
from .bases import DynamicChoiceForm, WechatAdmin

class MaterialAdmin(WechatAdmin):
    actions = ("delete_selected", "sync", )
    list_display = ("media_id", "type", "comment", "updatetime")
    list_filter = ("type", )
    search_fields = ("name", "media_id", "comment")

    fields = ("type", "media_id", "name", "url", "comment")
    readonly_fields = ("type", "media_id", "name", "url", "media_id")

    def preview(self, obj):
        if obj.type == Material.Type.IMAGE:
            return u'<img src="%s" />'%obj.url
    preview.short_description = "preview"
    preview.allow_tags = True

    def updatetime(self, obj):
        return timezone.datetime.fromtimestamp(obj.update_time)
    updatetime.short_description = "update time"

    def sync(self, request, queryset):
        app_id = self.get_request_app_id(request)
        app = WechatApp.get_by_id(app_id)
        try:
            materials = Material.sync(app)
            self.message_user(request, 
                "%d materials successfully synchronized"%len(materials))
        except Exception as e:
            self.message_user(request, 
                "sync failed with %s"%str(e), level=messages.ERROR)
    sync.short_description = _("sync")
    
    def delete_selected(self, request, obj):
        for o in obj.all():
            # TODO: 异常提示
            o.delete()
    delete_selected.short_description = "delete selected"

    def has_add_permission(self, request):
        return False

admin.site.register(Material, MaterialAdmin)