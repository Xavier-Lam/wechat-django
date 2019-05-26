# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


permissions = {
    "pay_full": _("Can full control %(appname)s WeChat pay"),
    "pay_manage": _("Can manage %(appname)s WeChat pay"),
    "pay_order": _("Can view %(appname)s WeChat pay orders")
}


permission_required = {
    "pay_full": {
        "pay_manage",
        "pay_order"
    },
    "pay_manage": {
        "wechat_django_pay.add_wechatpay",
        "wechat_django_pay.delete_wechatpay",
        "wechat_django_pay.change_wechatpay"
    }
}
