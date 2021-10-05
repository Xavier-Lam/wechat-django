import base64
from contextlib import contextmanager
import os
from tempfile import NamedTemporaryFile

from wechatpy import (WeChatClient as BaseWeChatClient,
                      WeChatComponent as BaseWeChatComponent,
                      WeChatPay as BaseWeChatPay)
from wechatpy.client import WeChatComponentClient as BaseWeChatComponentClient

from wechat_django.enums import AppType
from .crypto import crypto


class WeChatClient(BaseWeChatClient):
    ACCESSTOKEN_URL = None

    def __init__(self, app):
        self.app = app
        if app.access_token_url:
            self.ACCESSTOKEN_URL = app.access_token_url
        appsecret = crypto.decrypt(app.appsecret)
        super().__init__(app.appid, appsecret, session=app.session)

    def _fetch_access_token(self, url, params):
        """自定义accesstoken url"""
        return super()._fetch_access_token(self.ACCESSTOKEN_URL or url,
                                           params)


@contextmanager
def load_cert(self):
    if self._mch_cert and self._mch_key:
        # 证书文件要在硬盘上读取
        # 自动delete在windows下读取时报PermissionDenied
        # TODO: 可以考虑第一次使用时写入证书 析构时移除证书 减少IO
        with NamedTemporaryFile("wb", delete=False) as mch_cert,\
             NamedTemporaryFile("wb", delete=False) as mch_key:
            mch_cert.write(base64.b64decode(self._mch_cert))
            mch_cert.flush()
            mch_cert.close()
            mch_key.write(base64.b64decode(self._mch_key))
            mch_key.flush()
            mch_key.close()
            self.mch_cert = mch_cert.name
            self.mch_key = mch_key.name
            try:
                yield
            finally:
                if self.mch_key and os.path.exists(self.mch_key):
                    os.remove(self.mch_key)
                    self.mch_key = None
                if self.mch_cert and os.path.exists(self.mch_cert):
                    os.remove(self.mch_cert)
                    self.mch_cert = None
    else:
        yield


class WeChatPay(BaseWeChatPay):
    def __init__(self, pay, app=None):
        if pay.type == AppType.PAY:
            payer = pay
            kwargs = dict(
                appid=app.appid
            )
        else:
            payer = pay.parent
            kwargs = dict(
                appid=payer.appid,
                sub_mch_id=pay.mchid
            )
            if app:
                kwargs["sub_appid"] = app.appid
        kwargs.update(
            api_key=crypto.decrypt(payer.api_key),
            mch_id=payer.mchid
        )
        super().__init__(**kwargs)
        self.pay = pay
        self.app = app
        self._mch_cert = crypto.decrypt(payer.mch_cert).encode()
        self._mch_key = crypto.decrypt(payer.mch_key).encode()

    def _request(self, method, url_or_endpoint, **kwargs):
        with load_cert(self):
            return super()._request(method, url_or_endpoint, **kwargs)


class WeChatComponent(BaseWeChatComponent):
    def __init__(self, app):
        self.app = app
        super().__init__(app.appid,
                         crypto.decrypt(app.appsecret),
                         crypto.decrypt(app.token),
                         crypto.decrypt(app.encoding_aes_key),
                         session=app.session)

    def query_auth(self, authorization_code):
        raise NotImplementedError

    def cache_component_verify_ticket(self, msg, signature, timestamp, nonce):
        raise NotImplementedError

    def get_client_by_appid(self, authorizer_appid):
        raise NotImplementedError

    def get_client_by_authorization_code(self, authorization_code):
        raise NotImplementedError


class WeChatComponentClient(BaseWeChatComponentClient):
    def __init__(self, app):
        self.app = app
        # 父类的构造函数缓存有所冲突,直接调用祖先构造函数
        BaseWeChatClient.__init__(self, app.appid, '', session=app.session)
        self.component = app.parent.client

    @property
    def refresh_token(self):
        return self.app.refresh_token

    def fetch_access_token(self):
        result = super().fetch_access_token()
        # 更新refresh_token
        if result.get("authorizer_refresh_token"):
            self.app.refresh_token = result["authorizer_refresh_token"]
        return result
