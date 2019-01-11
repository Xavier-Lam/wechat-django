from django.db import models
from wechatpy import WeChatClient

class WechatApp(models.Model):
    class EncodingMode(object):
        PLAIN = 0
        BOTH = 1
        SAFE = 2

    title = models.CharField(max_length=16, null=False)
    name = models.CharField(max_length=16, blank=False, null=False, 
        unique=True) # readonly
    desc = models.TextField(default="", blank=True)

    appid = models.CharField(max_length=32, null=False, unique=True) # readonly
    appsecret = models.CharField(max_length=64, null=False)
    token = models.CharField(max_length=32, null=False)
    encoding_aes_key = models.CharField(max_length=43, null=False)
    encoding_mode = models.PositiveSmallIntegerField(choices=(
        (EncodingMode.PLAIN, "plain"),
        (EncodingMode.BOTH, "both"),
        (EncodingMode.SAFE, "safe")
    ), default=EncodingMode.PLAIN)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def sync_replies(self):
        replies = self.client.message.get_autoreply_info()
        

    def sync_menus(self):
        pass

    def match(self, message):
        if not message: return
        for handler in self.message_handlers:
            if handler.match(message):
                return handler

    @property
    def client(self):
        if not self._client:
            self._client = WeChatClient(
                self.appid,
                self.secret
                # TODO: 配置session
            )
        return self._client