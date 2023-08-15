from django.urls import re_path as url
from django.contrib import admin

import wechat_django

import wechat.rest
import wechat.views

admin.site.site_title = "WeChat-Django Admin"
admin.site.site_header = "WeChat-Django示例后台"

urlpatterns = [
    url(r'^admin/', admin.site.urls), #!wechat_django 在admin中添加wechat_django
    url(r'^wechat/', wechat_django.sites.wechat.urls), #!wechat_django 添加wechat_django
    url(r'^debug/oauth', wechat.views.oauth),
    url(r'^debug/rest', wechat.rest.TestAPIView.as_view())
]
