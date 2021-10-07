from django.contrib import admin
from django.conf.urls import url

import wechat_django


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^wechat/', wechat_django.site.urls),
]
