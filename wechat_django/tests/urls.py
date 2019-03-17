# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.conf.urls import url

import wechat_django

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r"^wechat/", wechat_django.sites.wechat.urls)
]
