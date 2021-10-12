from wechat_django.enums import AppType

from wechat_django.models import apps
from ..base import WeChatDjangoTestCase


class ApplicationQuerySetTestCase(WeChatDjangoTestCase):
    def test_get_ordinary_application(self):
        """测试获取一般app"""
        # 小程序
        app = apps.Application.objects.get(name=self.miniprogram.name)
        self.assertEqual(app.id, self.miniprogram.id)
        self.assertIsInstance(app, apps.MiniProgramApplication)
        app = apps.MiniProgramApplication.objects.get(
            name=self.miniprogram.name)
        self.assertEqual(app.id, self.miniprogram.id)
        self.assertIsInstance(app, apps.MiniProgramApplication)

        # 公众号
        app = apps.Application.objects.get(name=self.officialaccount.name)
        self.assertEqual(app.id, self.officialaccount.id)
        self.assertIsInstance(app, apps.OfficialAccountApplication)
        self.assertEqual(app.token, self.officialaccount.token)
        self.assertEqual(app.encoding_aes_key,
                         self.officialaccount.encoding_aes_key)
        app = apps.OfficialAccountApplication.objects.get(
            name=self.officialaccount.name)
        self.assertEqual(app.id, self.officialaccount.id)
        self.assertIsInstance(app, apps.OfficialAccountApplication)

        # web
        app = apps.Application.objects.get(name=self.webapp.name)
        self.assertEqual(app.id, self.webapp.id)
        self.assertIsInstance(app, apps.OrdinaryApplication)

    def test_get_pay(self):
        """测试获取支付app"""
        # 一般商户
        app = apps.Application.objects.get(name=self.pay.name)
        self.assertEqual(app.id, self.pay.id)
        self.assertIsInstance(app, apps.PayApplication)
        self.assertEqual(app.mchid, self.pay.mchid)
        self.assertEqual(app.api_key, self.pay.api_key)
        app = apps.PayApplication.objects.get(name=self.pay.name)
        self.assertEqual(app.id, self.pay.id)
        self.assertIsInstance(app, apps.PayApplication)

        # 服务商
        app = apps.Application.objects.get(name=self.merchant.name)
        self.assertEqual(app.id, self.merchant.id)
        self.assertIsInstance(app, apps.PayMerchant)
        self.assertEqual(app.mchid, self.merchant.mchid)
        self.assertEqual(app.api_key, self.merchant.api_key)
        app = apps.PayMerchant.objects.get(name=self.merchant.name)
        self.assertEqual(app.id, self.merchant.id)
        self.assertIsInstance(app, apps.PayMerchant)

        # 子商户
        app = apps.Application.objects.get(name=self.hosted_pay.name)
        self.assertEqual(app.id, self.hosted_pay.id)
        self.assertIsInstance(app, apps.HostedPayApplication)
        self.assertEqual(app.mchid, self.hosted_pay.mchid)
        self.assertEqual(app.api_key, self.hosted_pay.api_key)
        app = apps.HostedPayApplication.objects.get(name=self.hosted_pay.name)
        self.assertEqual(app.id, self.hosted_pay.id)
        self.assertIsInstance(app, apps.HostedPayApplication)

    def test_get_thirdpartyplatform(self):
        """测试获取第三方平台app"""
        # 第三方平台
        app = apps.Application.objects.get(name=self.thirdpartyplatform.name)
        self.assertEqual(app.id, self.thirdpartyplatform.id)
        self.assertIsInstance(app, apps.ThirdPartyPlatform)
        self.assertEqual(app.token, self.thirdpartyplatform.token)
        self.assertEqual(app.encoding_aes_key,
                         self.thirdpartyplatform.encoding_aes_key)
        app = apps.ThirdPartyPlatform.objects.get(
            name=self.thirdpartyplatform.name)
        self.assertEqual(app.id, self.thirdpartyplatform.id)
        self.assertIsInstance(app, apps.ThirdPartyPlatform)

        # 托管小程序
        app = apps.Application.objects.get(
            name=self.hosted_miniprogram.name)
        self.assertEqual(app.id, self.hosted_miniprogram.id)
        self.assertIsInstance(app, apps.MiniProgramAuthorizerApplication)
        app = self.thirdpartyplatform.children.get(
            name=self.hosted_miniprogram.name)
        self.assertEqual(app.id, self.hosted_miniprogram.id)
        self.assertIsInstance(app, apps.MiniProgramAuthorizerApplication)
        self.assertEqual(app.type, AppType.HOSTED | AppType.MINIPROGRAM)

        # 托管公众号
        app = apps.Application.objects.get(
            name=self.hosted_officialaccount.name)
        self.assertEqual(app.id, self.hosted_officialaccount.id)
        self.assertIsInstance(app, apps.OfficialAccountAuthorizerApplication)
        app = self.thirdpartyplatform.children.get(
            name=self.hosted_officialaccount.name)
        self.assertEqual(app.id, self.hosted_officialaccount.id)
        self.assertIsInstance(app, apps.OfficialAccountAuthorizerApplication)
        self.assertEqual(app.type, AppType.HOSTED | AppType.OFFICIALACCOUNT)
