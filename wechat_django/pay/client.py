# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from tempfile import NamedTemporaryFile

from wechatpy import WeChatPay as _Pay


class WeChatPayClient(_Pay):
    def __init__(self, pay):
        """:type pay: wechat_django.models.WeChatPay"""
        self.pay = pay
        kwargs = dict(
            appid=pay.appid,
            api_key=pay.api_key,
            mch_id=pay.mch_id,
            sub_mch_id=pay.sub_mch_id
        )
        if pay.mch_app_id:
            kwargs["sub_appid"] = pay.sub_appid

        super(WeChatPayClient, self).__init__(**kwargs)

    def _request(self, *args, **kwargs):
        if self.pay.mch_cert and self.pay.mch_key:
            # 证书文件要在硬盘上读取
            # 自动delete在windows下读取时报PermissionDenied
            # TODO: 可以考虑第一次使用时写入证书 析构时移除证书 减少IO
            with NamedTemporaryFile("wb", delete=False) as mch_cert,\
                NamedTemporaryFile("wb", delete=False) as mch_key:
                mch_cert.write(self.pay.mch_cert)
                mch_cert.flush()
                mch_cert.close()
                mch_key.write(self.pay.mch_key)
                mch_key.flush()
                mch_key.close()
                self.mch_cert = mch_cert.name
                self.mch_key = mch_key.name
                try:
                    return super(WeChatPayClient, self)._request(
                        *args, **kwargs)
                finally:
                    self.mch_key and os.path.exists(self.mch_key)\
                        and os.remove(self.mch_key)
                    self.mch_key = None
                    self.mch_cert and os.path.exists(self.mch_cert)\
                        and os.remove(self.mch_cert)
                    self.mch_cert = None
        else:
            return super(WeChatPayClient, self)._request(*args, **kwargs)
