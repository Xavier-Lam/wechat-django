# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import response

from ..sites.wechat import WeChatSite, WeChatViewSet
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

        class TestViewSet(WeChatViewSet):
            def test_view(self, request):
                return response.HttpResponse(status=204)
        
        # 在app_queryset中的公众号可访问,否则404
        site = TestSite()
        site.register(TestViewSet)
        viewset = site.get_registered(TestViewSet)
        view = viewset.wechat_view(viewset.test_view)
        resp = view(self.rf().get("/"), self.app.name)
        self.assertEqual(resp.status_code, 204)
        self.assertRaises(
            response.Http404, view, self.rf().get("/"), self.another_app.name)

    def test_wechat_view(self):
        """测试wechat_view"""
        that = self
        class ViewSet(WeChatViewSet):
            def test_view(self, request):
                return response.HttpResponse(status=204)

            def test_request_view(self, request):
                that.assertEqual(request.wechat.app.id, that.app.id)
                that.assertEqual(request.wechat.appname, that.app.name)
                return response.HttpResponse(status=204)

        # 测试http method正确
        viewset = ViewSet(WeChatSite())
        view = viewset.wechat_view(viewset.test_view, methods=("POST",))
        resp = view(self.rf().get("/"), self.app.name)
        self.assertEqual(resp.status_code, 405)
        resp = view(self.rf().post("/"), self.app.name)
        self.assertEqual(resp.status_code, 204)

        # 测试原view经过wechat_view后request能拿到WeChatInfo对象
        view = viewset.wechat_view(viewset.test_request_view)
        resp = view(self.rf().get("/"), self.app.name)
        self.assertEqual(resp.status_code, 204)
