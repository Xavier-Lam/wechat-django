# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from contextlib import contextmanager
import os
from tempfile import NamedTemporaryFile

from wechatpy import WeChatPay as _Pay
from wechatpy.exceptions import WeChatPayException


@contextmanager
def load_cert(self):
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
                yield
            finally:
                self.mch_key and os.path.exists(self.mch_key)\
                    and os.remove(self.mch_key)
                self.mch_key = None
                self.mch_cert and os.path.exists(self.mch_cert)\
                    and os.remove(self.mch_cert)
                self.mch_cert = None
    else:
        yield


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

    def _request(self, method, url_or_endpoint, **kwargs):
        logger = self.pay.app.logger("client")
        log_args = dict(data=kwargs.get("data", ""))
        with load_cert(self):
            try:
                rv = super(WeChatPayClient, self)._request(
                    method, url_or_endpoint, **kwargs)
            except WeChatPayException as e:
                log_args["err"] = e
                logger.warning(
                    "An error occurred when send wechat pay"
                    "request: %s" % log_args, exc_info=True)
                raise
            except Exception as e:
                log_args["err"] = e
                logger.error(
                    "An unexcept error occurred when send wechat pay"
                    "request: %s" % log_args, exc_info=True)
                raise
            else:
                log_args["result"] = rv
                logger.debug("A WeChat pay request sent: %s" % log_args)
            return rv


class WeChatPaySandboxClient(WeChatPayClient):
    def __init__(self, pay):
        super(WeChatPaySandboxClient, self).__init__(pay)
        self.sandbox = True
