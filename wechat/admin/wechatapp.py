from django.contrib import admin

from ..models import WechatApp

class WechatAppAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        fields = super().get_fields(request, obj)
        if obj:
            fields.remove("encoding_aes_key")
        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        return fields + ("name")