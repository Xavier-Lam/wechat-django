from django import forms
from django.contrib import admin, messages
from django.db import models as m
from django.utils import timezone
from django.utils.translation import ugettext as _

from ..models import Article, WeChatApp
from .bases import DynamicChoiceForm, WeChatAdmin

class ArticleAdmin(WeChatAdmin):
    actions = ("sync", )
    list_display = ("title", "author", "digest", "url", 
        "content_source_url", "synced_at")
    search_fields = ("title", "digest", "content")

    fields = ("title", "author", "digest", "url", "content_source_url")
    readonly_fields = ("type", "media_id", "name", "url", "media_id")

    def sync(self, request, queryset):
        app_id = self.get_request_app_id(request)
        app = WeChatApp.get_by_id(app_id)
        try:
            materials = Article.sync(app)
            self.message_user(request, 
                "%d articles successfully synchronized"%len(materials))
        except Exception as e:
            self.message_user(request, 
                "sync failed with %s"%str(e), level=messages.ERROR)
    sync.short_description = _("sync")

    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(Article, ArticleAdmin)