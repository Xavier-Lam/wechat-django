from django.conf.urls import url
from django.http.response import HttpResponse

from wechat_django.models import WeChatSNSScope
from wechat_django.oauth import wechat_auth

#!wechat_django oauth示例
@wechat_auth("debug")
def oauth(request):
    return HttpResponse(str(request.wechat.user).encode())