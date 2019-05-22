# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.admin.base import WeChatModelAdmin


class WeChatPayModelAdmin(WeChatModelAdmin):
    def get_queryset(self, request):
        return (super(WeChatModelAdmin, self)
            .get_queryset(request).prefetch_related("pay__app")
            .filter(pay_id=request.app_id))
