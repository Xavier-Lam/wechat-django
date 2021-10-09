from urllib.parse import urlencode

from django.contrib.admin import site
from django.contrib.auth.models import User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.middleware.common import CommonMiddleware
from django.test import TestCase
from django.test.client import RequestFactory
from django.urls.base import reverse
from httmock import HTTMock, response, urlmatch

from wechat_django.enums import AppType
from wechat_django.models import apps
from wechat_django.utils.crypto import crypto


def wechatapi(api, data="", callback=None):
    @urlmatch(netloc=r"(.*\.)?api\.weixin\.qq\.com$", path=api)
    def wechatapi_mock(url, request):
        if url.path != api:
            return response(404)
        headers = {
            "Content-Type": "application/json"
        }
        resp = response(200, data, headers)
        if callback:
            callback(url, request, response)
        return resp

    return HTTMock(wechatapi_mock)


class TestOnlyException(Exception):
    @classmethod
    def throw(cls, *args, **kwargs):
        raise cls(*args, **kwargs)


class WeChatDjangoTestCase(TestCase):
    APPSECRET = "appsecret"
    ENCODING_AES_KEY = "yguy3495y79o34vod7843933902h9gb2834hgpB90rg"
    TOKEN = "token"

    API_KEY = "api_key"
    MCH_CERT = b"mch_cert"
    MCH_KEY = b"mch_key"

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        apps.MiniProgramApplication.objects.create(
            title="miniprogram_title",
            name="miniprogram",
            appid="miniprogram_appid",
            appsecret=crypto.encrypt(cls.APPSECRET, raw=True),
            token=crypto.encrypt(cls.TOKEN),
            encoding_aes_key=crypto.encrypt(cls.ENCODING_AES_KEY)
        )
        apps.OfficialAccountApplication.objects.create(
            title="officialaccount_title",
            name="officialaccount",
            appid="officialaccount_appid",
            appsecret=crypto.encrypt(cls.APPSECRET, raw=True),
            token=crypto.encrypt(cls.TOKEN),
            encoding_aes_key=crypto.encrypt(cls.ENCODING_AES_KEY)
        )

        apps.PayApplication.objects.create(
            title="pay_title",
            name="pay",
            type=AppType.PAY,
            mchid="pay_mchid",
            api_key=crypto.encrypt(cls.API_KEY, raw=True),
            mch_cert=crypto.encrypt(cls.MCH_CERT),
            mch_key=crypto.encrypt(cls.MCH_KEY)
        )
        merchant = apps.PayMerchant.objects.create(
            title="merchant_title",
            name="merchant",
            type=AppType.MERCHANTPAY,
            appid="merchant_appid",
            mchid="merchant_mchid",
            api_key=crypto.encrypt(cls.API_KEY, raw=True),
            mch_cert=crypto.encrypt(cls.MCH_CERT),
            mch_key=crypto.encrypt(cls.MCH_KEY)
        )
        # TODO: 暂时不支援通过children创建,无法将Model转化为子类型
        apps.HostedPayApplication.objects.create(
            parent=merchant,
            title="hosted_pay_title",
            name="hosted_pay",
            type=AppType.HOSTED | AppType.PAY,
            mchid="hosted_pay_mchid"
        )

        thirdpartyplatform = apps.ThirdPartyPlatform.objects.create(
            title="thirdpartyplatform_title",
            name="thirdpartyplatform",
            appid="thirdpartyplatform_appid",
            appsecret=crypto.encrypt(cls.APPSECRET, raw=True),
            token=crypto.encrypt(cls.TOKEN),
            encoding_aes_key=crypto.encrypt(cls.ENCODING_AES_KEY)
        )
        thirdpartyplatform.children.create(
            title="hosted_miniprogram_title",
            name="thirdpartyplatform.miniprogram",
            appid="hosted_miniprogram_appid",
            type=AppType.HOSTED | AppType.MINIPROGRAM
        )
        thirdpartyplatform.children.create(
            title="hosted_officialaccount_title",
            name="thirdpartyplatform.officialaccount",
            appid="hosted_officialaccount_appid",
            type=AppType.HOSTED | AppType.OFFICIALACCOUNT
        )

        apps.Application.objects.create(
            title="unknown_title",
            name="unknown",
            type=AppType.UNKNOWN,
            appid="unknown_appid"
        )
        apps.Application.objects.create(
            title="webapp_title",
            name="webapp",
            type=AppType.WEBAPP,
            appid="webapp_appid"
        )

        superuser = User.objects.create(username="superadmin",
                                        is_superuser=True, is_staff=True)
        superuser.set_password("123456")
        superuser.save()

    def setUp(self):
        self.miniprogram = self.get_app("miniprogram")
        self.officialaccount = self.get_app("officialaccount")
        self.pay = self.get_app("pay")
        self.merchant = self.get_app("merchant")
        self.hosted_pay = self.get_app("hosted_pay")
        self.thirdpartyplatform = self.get_app("thirdpartyplatform")
        self.hosted_miniprogram = self.get_app(
            "thirdpartyplatform.miniprogram")
        self.hosted_officialaccount = self.get_app(
            "thirdpartyplatform.officialaccount")
        self.unknown = self.get_app("unknown")
        self.webapp = self.get_app("webapp")

        self.superadmin = User.objects.get(username="superadmin")

    def get_app(self, name):
        return apps.Application.objects.get(name=name)

    def get_model_admin(self, model):
        return site._registry[model]

    def get_admin_url(self, model, view, args=None, kwargs=None, query=None):
        args = args or tuple()
        kwargs = kwargs or dict()
        query = query or dict()
        url = reverse("admin:{app_label}_{model_name}_{view}".format(
            app_label=model._meta.app_label,
            model_name=model._meta.model_name,
            view=view
        ), args=args, kwargs=kwargs)
        if query:
            url += "?" + urlencode(query)
        return url

    def make_request(self, method, *args, **kwargs):
        user = kwargs.pop("user", None)
        wechat_app = kwargs.pop("wechat_app", None)
        rf = RequestFactory()
        request = getattr(rf, method.lower())(*args, **kwargs)
        SessionMiddleware().process_request(request)
        CommonMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        user and setattr(request, "user", user)
        wechat_app and setattr(request, "wechat_app", wechat_app)
        return request
