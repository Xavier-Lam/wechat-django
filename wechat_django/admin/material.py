from django import forms
from django.contrib import admin, messages
from django.db import models as m
from django.urls import reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from wechatpy.exceptions import WeChatException

from .. import views
from ..models import Material, WeChatApp
from .bases import DynamicChoiceForm, WeChatAdmin

class MaterialAdmin(WeChatAdmin):
    __category__ = "material"

    actions = ("delete_selected", "sync", )
    list_display = ("media_id", "type", "comment", "updatetime")
    list_filter = ("type", )
    search_fields = ("name", "media_id", "comment")

    fields = ("type", "media_id", "name", "open", "comment")
    readonly_fields = ("type", "media_id", "name", "open", "media_id")

    def preview(self, obj):
        if obj.type == Material.Type.IMAGE:
            return u'<img src="%s" />'%obj.url
    preview.short_description = _("preview")
    preview.allow_tags = True

    def updatetime(self, obj):
        return timezone.datetime.fromtimestamp(obj.update_time)
    updatetime.short_description = _("update time")

    def open(self, obj):
        blank = True
        request = self.request
        if obj.type == Material.Type.NEWS:
            url = "{0}?{1}".format(
                reverse("admin:wechat_django_article_changelist"),
                urlencode(dict(
                    app_id=self.get_app(request).id,
                    material_id=obj.id
                ))
            )
            blank = False
        elif obj.type == Material.Type.VOICE:
            # 代理下载
            app = self.get_app(request)
            url = reverse(views.material_proxy, kwargs=dict(
                appname=app.name,
                media_id=obj.media_id
            ))
        else:
            url = obj.url
        return '<a href="{0}" {1}>{2}</a>'.format(
            url, 'target="_blank"' if blank else "", _("open")
        )
    open.short_description = _("open")
    open.allow_tags = True

    def sync(self, request, queryset):
        self.check_wechat_permission(request, "sync")
        app = self.get_app(request)
        try:
            materials = Material.sync(app)
            self.message_user(request, 
                "%d materials successfully synchronized"%len(materials))
        except Exception as e:
            msg = "sync failed with {0}".format(e)
            if isinstance(e, WeChatException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    sync.short_description = _("sync")
    
    def delete_selected(self, request, obj):
        for o in obj.all():
            try:
                o.delete()
            except WeChatException:
                msg = "delete material failed: {0}".format(obj)
                self.logger(request).warning(msg, exc_info=True)
                raise
    delete_selected.short_description = _("delete selected")

    def has_add_permission(self, request):
        return False

admin.site.register(Material, MaterialAdmin)