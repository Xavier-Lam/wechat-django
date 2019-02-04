from functools import wraps
import logging

from django.conf.urls import url
from django.http import response
from django.shortcuts import get_object_or_404
import requests
from wechatpy import parse_message
from wechatpy.exceptions import InvalidSignatureException, WeChatClientException
from wechatpy.utils import check_signature

from . import utils
from .exceptions import WeChatApiError
from .models import MessageHandler, WeChatApp

__all__ = ("handler", "material_proxy", "urls")

url_patterns = []

def wechat_route(route, methods=None, name=""):
    if not methods:
        methods = ("GET",)
    def decorator(func):
        @wraps(func)
        def decorated_func(request, *args, **kwargs):
            if request.method not in methods:
                return response.HttpResponseNotAllowed(methods)
                
            return func(request, *args, **kwargs)

        pattern = url(
            r"^(?P<appname>[-_a-zA-Z\d]+)/" + route,
            decorated_func,
            name=name or func.__name__
        )
        url_patterns.append(pattern)
        return decorated_func
    return decorator

@wechat_route("$", methods=("GET", "POST"))
def handler(request, appname):
    """接收及处理微信发来的消息
    
    :type request: django.http.request.HttpRequest
    """
    app = get_object_or_404(WeChatApp, name=appname)
    logger = logging.getLogger("wechat.handler.{0}".format(appname))
    log_args = dict(params=request.GET, body=request.body, 
        ip=utils.get_ip(request))
    logger.debug("received: {0}".format(log_args))

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
        return response.HttpResponse(status=400)

    raw = request.body
    try:
        if app.encoding_mode == WeChatApp.EncodingMode.SAFE:
            crypto = WeChatCrypto(
                app.token, 
                app.encoding_aes_key, 
                app.appid
            )
            raw_msg = crypto.decrypt_message(
                raw,
                request.GET["signature"],
                request.GET["timestamp"],
                request.GET["nonce"]
            )
        msg = parse_message(raw)
    except:
        logger.error(
            "decrypt message failed: {0}".format(log_args),
            exc_info=True
        )
        return ""

    msg.raw = raw_msg
    msg.request = request
    handlers = MessageHandler.match(app, msg)
    if not handlers:
        logger.debug("handler not found: {0}".format(log_args))
        return ""
    handler = handlers[0]
    try:
        xml = handler.reply(msg)
        log_args["response"] = xml
        logger.debug("response: {0}".format(log_args))
    except:
        logger.warning("an error occurred when response: {0}".format(
            log_args), exc_info=True)
        return ""
    return response.HttpResponse(xml, content_type="text/xml")

@wechat_route(r"materials/(?P<media_id>[_a-zA-Z\d]+)$")
def material_proxy(request, appname, media_id):
    """代理下载微信的素材"""
    # TODO: cache
    app = WeChatApp.get_by_name(appname)
    if not app:
        return response.Http404()

    try:
        resp = app.client.material.get(media_id)
    except WeChatClientException as e:
        if e.errcode == WeChatApiError.INVALIDMEDIAID:
            return response.Http404()
        logging.getLogger("wechat.views.{0}".format(appname)).warning(
            "an exception occurred when download material",
            exc_info=True)
        return response.HttpResponseServerError()
    if not isinstance(resp, requests.Response):
        # 暂时只处理image和voice
        return response.Http404()
    
    rv = response.FileResponse(resp.content)
    for k, v in resp.headers.items():
        if k.lower().startswith("content-"):
            rv[k] = v
    return rv

urls = (url_patterns, "", "")