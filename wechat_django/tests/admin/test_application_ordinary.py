from django.urls.base import reverse
from django.utils.translation import ugettext_lazy as _

from wechat_django.models import apps
from ..base import WeChatDjangoTestCase


class AdminOrdinaryApplicationTestCase(WeChatDjangoTestCase):
    def test_ordinary_accessibility(self):
        """测试一般app后台可访问性"""
        model = apps.OrdinaryApplication
        admin = self.get_model_admin(model)
        app = self.unknown

        url = self.get_admin_url(model, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.changelist_view(request)
        self.assertEqual(resp.status_code, 200)
        resp.render()
        add_officialaccount = '<a href="{href}">{text}</a>'.format(
            href=reverse("admin:{0}_{1}_add".format(
                apps.OfficialAccountApplication._meta.app_label,
                apps.OfficialAccountApplication._meta.model_name)),
            text=_("Add an official account")
        )
        self.assertInHTML(add_officialaccount, resp.content.decode())
        add_miniprogram = '<a href="{href}">{text}</a>'.format(
            href=reverse("admin:{0}_{1}_add".format(
                apps.MiniProgramApplication._meta.app_label,
                apps.MiniProgramApplication._meta.model_name)),
            text=_("Add a miniprogram")
        )
        self.assertInHTML(add_miniprogram, resp.content.decode())

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

    def test_web_accessibility(self):
        """测试webapp后台可访问性"""
        model = apps.OrdinaryApplication
        admin = self.get_model_admin(model)
        app = self.webapp

        url = self.get_admin_url(model, "change", args=(app.id,))
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(app.id))
        resp.render()
        self.assertEqual(resp.status_code, 200)

    def test_miniprogram_accessibility(self):
        """测试小程序app后台访问性"""
        model = apps.MiniProgramApplication
        admin = self.get_model_admin(model)
        app = self.miniprogram

        url = self.get_admin_url(model, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.changelist_view(request)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.url,
            self.get_admin_url(apps.OrdinaryApplication, "changelist"))

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

        url = self.get_admin_url(model, "change", args=(self.webapp.id,))
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(self.webapp.id))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/admin/")

    def test_officialaccount_accessibility(self):
        """测试公众号app后台访问性"""
        model = apps.OfficialAccountApplication
        admin = self.get_model_admin(model)
        app = self.officialaccount

        url = self.get_admin_url(model, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.changelist_view(request)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            resp.url,
            self.get_admin_url(apps.OrdinaryApplication, "changelist"))

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

        url = self.get_admin_url(model, "change", args=(self.webapp.id,))
        request = self.make_request("get", url, user=self.superadmin)
        resp = admin.change_view(request, str(self.webapp.id))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/admin/")

    def test_queryset(self):
        """测试后台查询集"""
        url = self.get_admin_url(apps.OrdinaryApplication, "changelist")
        request = self.make_request("get", url, user=self.superadmin)
        admin = self.get_model_admin(apps.OrdinaryApplication)
        applications = admin.get_queryset(request).all()
        self.assertEqual(len(applications), 4)
        self.assertIn(self.miniprogram, applications)
        self.assertIn(self.officialaccount, applications)
        self.assertIn(self.unknown, applications)
        self.assertIn(self.webapp, applications)
