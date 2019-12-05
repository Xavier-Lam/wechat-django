# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.http import urlencode
from wechatpy import WeChatOAuth

from wechat_django.constants import WeChatSNSScope, WeChatWebAppScope


class WeChatOAuthClient(WeChatOAuth):
    def __init__(self, app):
        self.OAUTH_URL = app.oauth_url or app.OAUTH_URL
        super(WeChatOAuthClient, self).__init__(app.appid, app.appsecret, "")

    def authorize_url(self, redirect_uri, scope=WeChatSNSScope.BASE, state=""):
        return self.OAUTH_URL + "?" + urlencode(dict(
            appid=self.app_id,
            redirect_uri=redirect_uri,
            response_type="code",
            scope=scope,
            state=state
        )) + "#wechat_redirect"

    def qrconnect_url(self, redirect_uri, state=""):
        return self.OAUTH_URL + "?" + urlencode(dict(
            appid=self.app_id,
            redirect_uri=redirect_uri,
            response_type="code",
            scope=WeChatWebAppScope.LOGIN,
            state=state
        )) + "#wechat_redirect"
