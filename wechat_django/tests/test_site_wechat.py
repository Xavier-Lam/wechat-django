# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import response

from ..sites.wechat import WeChatSite, WeChatView
from .base import WeChatTestCase


class WeChatSiteTestCase(WeChatTestCase):
    def test_patch_request(self):
        """测试patch_request,request能拿到wechat对象,并且各属性均正确"""
        # 测试基本的WeChatHttpRequest
        pass

        # 测试WeChatMessageRequest
        pass

        # 测试WeChatOAuthRequest
        pass

    def test_app_queryset(self):
        """测试app_queryset正确"""
        that = self
        class TestSite(WeChatSite):
            @property
            def app_queryset(self):
                return super(TestSite, self).app_queryset.filter(
                    name=that.app.name)

        class TestView(WeChatView):
            def get(self, request, appname):
                return response.HttpResponse(status=204)

            def _get_appname(self, request, appname):
                return appname

        # 在app_queryset中的公众号可访问,否则404
        site = TestSite()
        view = site._create_view(TestView)
        resp = view(self.rf().get("/"), self.app.name)
        self.assertEqual(resp.status_code, 204)
        resp = view(self.rf().get("/"), self.another_app.name)
        self.assertEqual(resp.status_code, 404)

    def test_wechat_view(self):
        """测试wechat_view"""
        that = self
        class View(WeChatView):
            def post(self, request):
                that.assertEqual(request.wechat.app.id, that.app.id)
                that.assertEqual(request.wechat.appname, that.app.name)
                return response.HttpResponse(status=204)

            def _get_appname(self, request, *args, **kwargs):
                return that.app.name

        # 测试app_queryset
        pass

        # 测试http method正确
        view = View.as_view()
        resp = view(self.rf().get("/"))
        self.assertEqual(resp.status_code, 405)
        resp = view(self.rf().post("/"))
        self.assertEqual(resp.status_code, 204)

        # 测试装饰器
        pass
