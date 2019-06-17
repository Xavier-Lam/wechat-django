# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
import object_tool

from ..models import UnifiedOrder, UnifiedOrderResult
from .base import WeChatPayModelAdmin


class OrderResultAdmin(admin.StackedInline):
    model = UnifiedOrderResult

    fields = (
        "transaction_id", "trade_state", "time_end", "settlement_total_fee",
        "cash_fee", "cash_fee_type", "coupon_fee", "bank_type", "detail",
        "is_subscribe", "sub_is_subscribe", "created_at", "updated_at")

    def get_fields(self, request, obj=None):
        rv = super(OrderResultAdmin, self).get_fields(request, obj)
        if not request.app.pay.sub_mch_id:
            rv = list(rv)
            rv.remove("sub_is_subscribe")
        return rv

    def get_readonly_fields(self, request, obj=None):
        return self.get_fields(request, obj)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrderAdmin(WeChatPayModelAdmin):
    __category__ = "order"
    __model__ = UnifiedOrder

    inlines = (OrderResultAdmin,)

    actions = ("sync",)
    list_display = (
        "out_trade_no", "body", "total_fee", "trade_state", "transaction_id",
        "openid", "sub_openid", "time_start", "time_expire", "created_at",
        "updated_at")

    change_object_tools = ("sync",)
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

    def sync(self, request, queryset_or_obj):
        self.check_wechat_permission(request, "change")

        if isinstance(queryset_or_obj, UnifiedOrder):
            queryset_or_obj = [queryset_or_obj]

        for obj in queryset_or_obj:
            obj.sync()
    sync.short_description = _("Sync order")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
