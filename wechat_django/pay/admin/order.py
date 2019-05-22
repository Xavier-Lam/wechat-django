# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from wechat_django.admin.utils import field_property, list_property
from ..models import UnifiedOrder
from .base import WeChatPayModelAdmin


class OrderAdmin(WeChatPayModelAdmin):
    __category__ = "order"
    __model__ = UnifiedOrder

    list_display = (
        "out_trade_no", "body", "total_fee", "trade_state", "transaction_id",
        "openid", "sub_openid", "time_start", "time_expire", "created_at",
        "updated_at")

    fields = (
        "out_trade_no", "body", "total_fee", "fee_type", "openid",
        "sub_openid", "time_start", "time_expire", "detail",
        "spbill_create_ip", "device_info", "goods_tag", "trade_type",
        "product_id", "limit_pay", "receipt", "scene_info", "comment",
        "created_at", "updated_at")

    def get_list_display(self, request):
        rv = super(OrderAdmin, self).get_list_display(request)
        if not request.app.pay.sub_mch_id:
            rv = list(rv)
            rv.remove("sub_openid")
        return rv

    def get_fields(self, request, obj=None):
        rv = super(OrderAdmin, self).get_fields(request, obj)
        if not request.app.pay.sub_mch_id:
            rv = list(rv)
            rv.remove("sub_openid")
        return rv

    def get_readonly_fields(self, request, obj=None):
        fields = list(self.get_fields(request, obj))
        fields.remove("comment")
        return fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
