from . import WeChatUser

class WeChatMessage(object):
    """由微信接收到的消息"""
    def __init__(self, app, message):
        self._app = app
        self._message = message

    @property
    def message(self):
        """
        :rtype: wechatpy.messages.BaseMessage
        """
        return self._message
    
    @property
    def app(self):
        """
        :rtype: wechat_django.models.WeChatApp
        """
        return self._app

    @property
    def user(self):
        """
        :rtype: wechat_django.models.WeChatUser
        """
        return WeChatUser.get_by_openid(self.app, self.message.source)