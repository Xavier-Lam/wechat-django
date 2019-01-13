from django import forms
from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.urls import reverse
from django.utils.translation import ugettext as _

from ..handler import handler
from ..models import WechatApp

class WechatAppAdmin(admin.ModelAdmin):
    list_display = ("title", "name", "appid", "short_desc", "_interactable", 
        "created", "updated")

    fields = ("title", "name", "appid", "appsecret", "token", "encoding_aes_key",
        "encoding_mode", "desc", "callback", "created", "updated")
    readonly_fields = ("callback", )

    def short_desc(self ,obj):
        return truncatechars(obj.desc, 35)
    short_desc.short_description = _("description")

    def callback(self, obj):
        return self.request.build_absolute_uri(reverse(handler, kwargs=dict(appname=obj.name)))

    def get_fields(self, request, obj=None):
        fields = list(super().get_fields(request, obj))
        if not obj:
            fields.remove("created")
            fields.remove("updated")
        return fields

    def get_readonly_fields(self, request, obj=None):
        rv = super().get_readonly_fields(request, obj)
        if obj:
            rv = rv + ("name", "appid", "created", "updated")
        return rv

    def get_queryset(self, request):
        self.request = request
        return super().get_queryset(request)
    
    class WechatAppForm(forms.ModelForm):
        class Meta(object):
            model = WechatApp
            fields = "__all__"
            widgets = dict(
                appsecret=forms.PasswordInput(render_value=True),
                encoding_aes_key=forms.PasswordInput(render_value=True)
            )

    form = WechatAppForm

admin.site.register(WechatApp, WechatAppAdmin)