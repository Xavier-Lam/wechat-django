# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin.filters import RelatedFieldListFilter
from django.utils.translation import ugettext_lazy as _

from wechat_django.admin.base import WeChatModelAdmin


class PayListFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        return [(pay.id, str(pay)) for pay in request.app.pays.all()]


class WeChatPayModelAdmin(WeChatModelAdmin):
    list_filter = (("pay", PayListFilter),)

    def get_queryset(self, request):
        parent = super(WeChatModelAdmin, self)
        return parent.get_queryset(request).filter(pay__app_id=request.app_id)

    def get_model_perms(self, request):
        if not request.app.abilities.pay:
            return {}
        return super(WeChatPayModelAdmin, self).get_model_perms(request)
