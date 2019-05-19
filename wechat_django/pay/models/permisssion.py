# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _


permissions = {
    "pay_manage": _("Can manage %(appname)s WeChat pay")
}


permission_required = {
    "pay_manage": {
        "wechat_django_pay.add_wechatpay",
        "wechat_django_pay.delete_wechatpay",
        "wechat_django_pay.change_wechatpay"
    }
}
