from urllib.parse import urlencode

from django.http.response import Http404

from wechat_django.models import apps
from ..base import WeChatDjangoTestCase


class AdminThirdPartyPlatformTestCase(WeChatDjangoTestCase):
    def test_thirdpartyplatform_accessibility(self):
        """测试第三方平台app后台可访问性"""
        model = apps.ThirdPartyPlatform
        admin = self.get_model_admin(model)
        app = self.thirdpartyplatform

        url = self.get_admin_url(model, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.changelist_view(request)
        resp.render()
        self.assertEqual(resp.status_code, 200)

        url = self.get_admin_url(model, "add")
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.add_view(request)
        resp.render()
        self.assertEqual(resp.status_code, 200)

        url = self.get_admin_url(model, "change", args=(app.id,))
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(app.id))
        resp.render()
        self.assertEqual(resp.status_code, 200)

        url = self.get_admin_url(model, "change", args=(self.miniprogram.id,))
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(self.miniprogram.id))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/admin/")

    def test_authorizer_accessibility(self):
        """测试第三方平台托管app后台可访问性"""
        model = apps.AuthorizerApplication
        admin = self.get_model_admin(model)
        app = self.hosted_miniprogram
        list_query = dict(parent_id=app.parent.id)
        query = dict(_changelist_filters=urlencode(list_query))

        url = self.get_admin_url(model, "changelist", query=list_query)
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.changelist_view(request)
        resp.render()
        self.assertEqual(resp.status_code, 200)

        url = self.get_admin_url(model, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        self.assertRaises(Http404,
                          lambda req: admin.changelist_view(req), request)

        url = self.get_admin_url(model, "add", query=query)
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.add_view(request)
        resp.render()
        self.assertEqual(resp.status_code, 200)

        url = self.get_admin_url(model, "change", args=(app.id,), query=query)
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(app.id))
        self.assertEqual(resp.status_code, 200)

        app = self.hosted_officialaccount

        url = self.get_admin_url(model, "change", args=(app.id,), query=query)
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(app.id))
        resp.render()
        self.assertEqual(resp.status_code, 200)

        url = self.get_admin_url(model, "change", args=(self.miniprogram.id,),
                                 query=query)
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(self.miniprogram.id))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/admin/")

    def test_queryset(self):
        """测试后台查询集"""
        url = self.get_admin_url(apps.ThirdPartyPlatform, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        admin = self.get_model_admin(apps.ThirdPartyPlatform)
        applications = admin.get_queryset(request).all()
        self.assertEqual(len(applications), 1)
        self.assertIn(self.thirdpartyplatform, applications)

        url = self.get_admin_url(apps.AuthorizerApplication, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        admin = self.get_model_admin(apps.AuthorizerApplication)
        applications = admin.get_queryset(request).all()
        self.assertEqual(len(applications), 2)
        self.assertIn(self.hosted_miniprogram, applications)
        self.assertIn(self.hosted_officialaccount, applications)
