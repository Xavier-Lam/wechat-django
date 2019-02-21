#encoding: utf-8
from django.conf import settings
from django.conf.urls import url
from django.http.response import HttpResponse

from wechat_django.decorators import message_handler
from wechat_django.models import WeChatUser
from wechat_django.oauth import wechat_auth, WeChatSNSScope
from wechatpy.replies import TextReply

#!wechat_django oauth示例
@wechat_auth(settings.SAMPLEAPPNAME)
def oauth(request):
    return HttpResponse(str(request.wechat.user).encode())

#!wechat_django 自定义业务示例
@message_handler
def custom_business(message):
    """
    :type message: wechat_django.models.WeChatMessageInfo
    """
    user = message.user
    msg = message.message
    text = "hello, {0}! we received a {1} message.".format(
        user, msg.type)
    return TextReply(content=text.encode())
