# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http import Http404, response

from ..models import WeChatApp
from ..sites.wechat import WeChatSite, WeChatView, wechat_view
from .base import mock, WeChatTestCase


class WeChatSiteTestCase(WeChatTestCase):
    def test_app_queryset(self):
        """测试app_queryset正确"""
        that = self
        class TestSite(WeChatSite):
            @property
            def app_queryset(self):
                return WeChatApp.objects.filter(name=that.app.name)

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
        self.assertRaises(Http404, view, self.rf().get("/"),
                          self.another_app.name)

    def test_wechat_view(self):
        """测试wechat_view"""
        that = self

        class View(WeChatView):
            app_queryset = WeChatApp.objects.filter(name=self.app.name)

            def post(self, request):
                that.assertEqual(request.wechat.app.id, that.app.id)
                that.assertEqual(request.wechat.appname, that.app.name)
                return response.HttpResponse(status=204)

            def _get_appname(self, request, *args, **kwargs):
                return that.app.name

        # 测试app_queryset
        with mock.patch.object(View, "_get_appname"):
            View._get_appname.return_value = self.another_app.name
            view = View.as_view()
            self.assertRaises(Http404, view, self.rf().post("/"))

        # 测试http method正确
        view = View.as_view()
        resp = view(self.rf().get("/"))
        self.assertEqual(resp.status_code, 405)
        resp = view(self.rf().post("/"))
        self.assertEqual(resp.status_code, 204)

        # 测试装饰器
        @wechat_view("^$", methods=["POST"])
        def View(request, appname):
            return response.HttpResponse(status=204)

        resp = View.as_view()(self.rf().get("/"), self.app.name)
        self.assertEqual(resp.status_code, 405)
        resp = View.as_view()(self.rf().post("/"), self.app.name)
        self.assertEqual(resp.status_code, 204)

    def test_request(self):
        """测试请求响应正常,路由匹配正常"""
        pass
