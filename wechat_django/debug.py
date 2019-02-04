from django.conf.urls import url
from django.http.response import HttpResponse

from .models import WeChatSNSScope
from .oauth import wechat_auth

@wechat_auth("debug")
def debug(request):
    return HttpResponse(str(request.wechat.user).encode())

urls = ((url(r"$", debug, name="debug"),), "", "")