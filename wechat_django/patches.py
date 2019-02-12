from django.utils.http import urlencode
import logging

from wechatpy import (exceptions as excs, WeChatClient as _WeChatClient, 
    WeChatOAuth as _WeChatOAuth)
from wechatpy.client import api

from .oauth import WeChatSNSScope

class WeChatMaterial(api.WeChatMaterial):
    def get_raw(self, media_id):
        return self._post(
            'material/get_material',
            data={
                'media_id': media_id
            }
        )

class WeChatClient(_WeChatClient):
    """继承原有WeChatClient添加日志功能 追加accesstoken url获取"""
    appname = None
    # 增加raw_get方法
    material = WeChatMaterial()

    ACCESSTOKEN_URL = None

    def _fetch_access_token(self, url, params):
        """自定义accesstoken url"""
        return super(WeChatClient, self)._fetch_access_token(
            self.ACCESSTOKEN_URL or url, params)
        
    def _request(self, method, url_or_endpoint, **kwargs):
        msg = self._log_msg(method, url_or_endpoint, **kwargs)
        self._logger("req").debug(msg)
        try:
            return super(WeChatClient, self)._request(
                method, url_or_endpoint, **kwargs)
        except:
            self._logger("excs").warning(msg, exc_info=True)
            raise

    def _handle_result(self, res, method=None, url=None,
        *args, **kwargs):
        msg = self._log_msg(method, url, **kwargs)
        try:
            msg += "\tresp:" + res.content
        except:
            msg += "\tresp:{0}".format(res)
        return super(WeChatClient, self)._handle_result(
            res, method, url, *args, **kwargs)

    def _logger(self, type):
        return logging.getLogger("wechat.api.{type}.{appname}".format(
            type=type, 
            appname=self.appname
        ))
    
    def _log_msg(self, method, url, **kwargs):
        msg = "{method}\t{url}".format(
            method=method,
            url=url
        )
        if kwargs.get("params"):
            msg += "\tparams:{0}".format(kwargs["params"])
        if kwargs.get("data"):
            msg += "\tdata:{0}".format(kwargs["data"])
        return msg

class WeChatOAuth(_WeChatOAuth):
    OAUTH_URL = "https://open.weixin.qq.com/connect/oauth2/authorize"
    QRCONNECT_URL = "https://open.weixin.qq.com/connect/qrconnect"

    def __init__(self, app_id, secret):
        super(WeChatOAuth, self).__init__(app_id, secret, "")

    def authorize_url(self, redirect_uri, scope=WeChatSNSScope.BASE, state=""):
        return self.OAUTH_URL + "?" + urlencode(dict(
            appid=self.app_id,
            redirect_uri=redirect_uri,
            response_type="code",
            scope=scope
        )) + "#wechat_redirect"
    
    def qrconnect_url(self, redirect_uri, state=""):
        return self.QRCONNECT_URL + "?" + urlencode(dict(
            appid=self.app_id,
            redirect_uri=redirect_uri,
            response_type="code",
            scope="snsapi_login"
        )) + "#wechat_redirect"