from functools import wraps

from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from wechatpy import parse_message
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature

from .models import WechatApp

def handler(request, appname):
    """接收及处理微信发来的消息
    
    :type request: django.http.request.HttpRequest
    """
    app = get_object_or_404(WechatApp, name=appname)

    try:
        check_signature(
            request.GET["token"],
            request.GET["signature"],
            request.GET["timestamp"],
            request.GET["nonce"]
        )
        if request.method == "GET":
            return request.GET["echostr"]
    except KeyError:
        return HttpResponse(status=400)

    raw = request.body
    try:
        if app.encoding_mode == WechatApp.EncodingMode.SAFE:
            crypto = WeChatCrypto(
                app.token, 
                app.encoding_aes_key, 
                app.appid
            )
            raw = crypto.decrypt_message(
                raw,
                request.GET["signature"],
                request.GET["timestamp"],
                request.GET["nonce"]
            )
        msg = parse_message(raw)
    except:
        # TODO: 异常处理
        return ""

    msg.raw = raw
    msg.request = request
    handler = app.match(msg)
    if not handler:
        return HttpResponse()
    xml = handler.reply(msg)
    return HttpResponse(xml, content_type="text/xml")