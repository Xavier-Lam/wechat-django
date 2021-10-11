from unittest.mock import patch
from urllib.parse import parse_qsl, urlparse

from wechatpy import WeChatComponent

from wechat_django.models.apps.base import Application
from wechat_django.views.thirdpartyplatform import ThirdPartyPlatformAuth
from ..base import WeChatDjangoTestCase


class ViewThirdPartyPlatformTestCase(WeChatDjangoTestCase):
    def test_authorize_flow(self):
        """测试完整流程"""
        app = self.hosted_officialaccount
        host = "wechat.django"
        url = ThirdPartyPlatformAuth.get_url(app.parent)

        # 初次请求,未授权
        pre_auth_code = "pre_auth_code"
        data = {
            "pre_auth_code": pre_auth_code,
            "expires_in": 600
        }
        with patch.object(WeChatComponent, "create_preauthcode",
                          return_value=data):
            response = self.client.get(url, HTTP_HOST=host, secure=True)
            WeChatComponent.create_preauthcode.assert_called_once()
        request = response.wsgi_request
        self.assertEqual(response.status_code, 302)

        parsed_url = urlparse(response.url)
        parsed_query = dict(parse_qsl(parsed_url.query))
        auth_url = "https://mp.weixin.qq.com/cgi-bin/componentloginpage"
        self.assertEqual(response.url.split("?")[0], auth_url)
        self.assertEqual(parsed_query["component_appid"], app.parent.appid)
        self.assertEqual(parsed_query["pre_auth_code"], pre_auth_code)
        full_url = request.build_absolute_uri(url)
        self.assertEqual(parsed_query["redirect_uri"], full_url)

        # 授权回来
        auth_code = "code"
        data = {
            "auth_code": auth_code,
            "expires_in": 600
        }
        access_token = "a"
        refresh_token = "r"
        auth_data = {
            "authorization_info": {
                "authorizer_appid": app.appid,
                "authorizer_access_token": access_token,
                "expires_in": 7200,
                "authorizer_refresh_token": refresh_token,
                "func_info": [
                    {"funcscope_category": {"id": 1}},
                    {"funcscope_category": {"id": 2}}
                ]
            }
        }
        with patch.object(WeChatComponent, "_query_auth",
                          return_value=auth_data):
            response = self.client.get(full_url, data, HTTP_HOST=host,
                                       secure=True)
            WeChatComponent._query_auth.assert_called_once_with(auth_code)
            app = Application.objects.get(name=app.name)
            self.assertEqual(app.access_token, access_token)
            self.assertEqual(app.refresh_token, refresh_token)
            func_info = auth_data["authorization_info"]["func_info"]
            self.assertEqual(app.storage["func_info"], func_info)

        # 清除测试数据
        del app._access_token
        del app.refresh_token

    def test_authorize_url(self):
        """测试url生成"""
        pass
