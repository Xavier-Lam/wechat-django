from wechat_django.models import apps
from .base import WeChatDjangoTestCase


class AdminPayApplicationTestCase(WeChatDjangoTestCase):
    def test_pay_accessibility(self):
        """测试一般商户后台可访问性"""
        model = apps.PayApplication
        admin = self.get_model_admin(model)
        app = self.pay

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

    def test_merchant_accessibility(self):
        """测试服务商后台可访问性"""
        model = apps.PayMerchant
        admin = self.get_model_admin(model)
        app = self.merchant

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

    def test_queryset(self):
        """测试后台查询集"""
        url = self.get_admin_url(apps.PayApplication, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        admin = self.get_model_admin(apps.PayApplication)
        applications = admin.get_queryset(request).all()
        self.assertEqual(len(applications), 1)
        self.assertIn(self.pay, applications)

        url = self.get_admin_url(apps.PayMerchant, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        admin = self.get_model_admin(apps.PayMerchant)
        applications = admin.get_queryset(request).all()
        self.assertEqual(len(applications), 1)
        self.assertIn(self.merchant, applications)

        url = self.get_admin_url(apps.HostedPayApplication, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        admin = self.get_model_admin(apps.HostedPayApplication)
        applications = admin.get_queryset(request).all()
        self.assertEqual(len(applications), 1)
        self.assertIn(self.hosted_pay, applications)
