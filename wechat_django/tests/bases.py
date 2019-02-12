from django.test import TestCase

from ..models import WeChatApp

class WeChatTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super(WeChatTestCase, cls).setUpTestData()
        WeChatApp.objects.create(title="test", name="test", 
            appid="appid", appsecret="secret")
        WeChatApp.objects.create(title="test1", name="test1", 
            appid="appid1", appsecret="secret")

    def setUp(self):
        self.app = WeChatApp.get_by_name("test") 