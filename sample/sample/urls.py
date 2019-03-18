#encoding: utf-8
"""sample URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin

import wechat_django

import wechat.views

admin.site.site_title = "WeChat-Django Admin"
admin.site.site_header = "WeChat-Django示例后台"

urlpatterns = [
    url(r'^admin/', admin.site.urls), #!wechat_django 在admin中添加wechat_django
    url(r'^wechat/', wechat_django.sites.wechat.urls), #!wechat_django 添加wechat_django
    url(r'^debug/oauth', wechat.views.oauth)
]
