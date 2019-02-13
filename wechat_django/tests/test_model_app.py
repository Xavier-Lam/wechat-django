from .bases import WeChatTestCase

from .interceptors import wechatapi, wechatapi_accesstoken, wechatapi_error


class AppTestCase(WeChatTestCase):
    def test_getaccesstoken(self):
        """测试accesstoken获取"""
        api = "/cgi-bin/token"
        # 测试获取accesstoken
        with wechatapi_accesstoken(lambda url, req, resp: self.assertTrue(req)):
            token = self.app.client.access_token
            self.assertEqual(token, "ACCESS_TOKEN")
        # 测试获取后不再请求accesstoken
        success = dict(
            errcode=0,
            errmsg=""
        )
        with wechatapi_error(api), wechatapi("/cgi-bin/message/custom/send", success):
            resp = self.app.client.message.send_text("openid", "abc")
            self.assertEqual(resp["errcode"], 0)
