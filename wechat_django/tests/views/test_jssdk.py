import json
import re
import time
from urllib.parse import urlencode

from django.urls import reverse

from ..base import WeChatDjangoTestCase


class JSSDKTestCase(WeChatDjangoTestCase):
    def test_jsconfig(self):
        """测试配置jssdk"""
        self.officialaccount._jsapi_ticket = "ticket"
        self.officialaccount._jsapi_ticket_expires_at = time.time() + 5
        self.hosted_officialaccount._jsapi_ticket = "ticket"
        self.hosted_officialaccount._jsapi_ticket_expires_at = time.time() + 5

        referrer = "https://baidu.com/index.html"
        js_api_list = ["onMenuShareTimeline", "onMenuShareAppMessage"]

        pattern = r"^wx\.config\(JSON\.parse\('(.+)'\)\);$"

        # 一般应用
        app = self.officialaccount
        path = reverse("wechat_django:jsconfig",
                       kwargs={"app_name": app.name})
        query = {"jsApiList": ",".join(js_api_list)}
        resp = self.client.get(path, QUERY_STRING=urlencode(query),
                               HTTP_REFERER=referrer)
        match = re.match(pattern, resp.content.decode())
        data = json.loads(match.group(1))
        self.assertEqual(data["appId"], app.appid)
        self.assertEqual(data["jsApiList"], js_api_list)
        signature = app.client.jsapi.get_jsapi_signature(
            data["nonceStr"], app.jsapi_ticket, data["timestamp"], referrer)
        self.assertEqual(data["signature"], signature)

        # 托管应用
        app = self.hosted_officialaccount
        path = reverse("wechat_django:jsconfig",
                       kwargs={"app_name": app.name})
        query = {"jsApiList": ",".join(js_api_list)}
        resp = self.client.get(path, QUERY_STRING=urlencode(query),
                               HTTP_REFERER=referrer)
        match = re.match(pattern, resp.content.decode())
        data = json.loads(match.group(1))
        self.assertEqual(data["appId"], app.appid)
        self.assertEqual(data["jsApiList"], js_api_list)
        signature = app.client.jsapi.get_jsapi_signature(
            data["nonceStr"], app.jsapi_ticket, data["timestamp"], referrer)
        self.assertEqual(data["signature"], signature)

        # 无referrer提示错误
        app = self.hosted_officialaccount
        path = reverse("wechat_django:jsconfig",
                       kwargs={"app_name": app.name})
        resp = self.client.get(path)
        match = re.match(r"console.error\((.+)\);", resp.content.decode())
        self.assertIsInstance(json.loads(match.group(1)), str)

        # 404
        app = self.thirdpartyplatform
        path = reverse("wechat_django:jsconfig",
                       kwargs={"app_name": app.name})
        resp = self.client.get(path)
        self.assertEqual(resp.status_code, 404)

        del self.officialaccount._jsapi_ticket
        del self.hosted_officialaccount._jsapi_ticket
