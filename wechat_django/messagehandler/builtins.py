import time

from wechatpy import events

from wechat_django.enums import AppType
from .base import MessageHandlerCollection, PlainTextReply


builtin_handlers = MessageHandlerCollection()
builtin_handlers.DEFAULT_PASSTHROUGH = True
builtin_handlers.DEFAULT_WEIGHT = 9999


def subscribe_matcher(message, request, *args, **kwargs):
    return isinstance(message, events.BaseEvent) and\
        message.event in ("subscribe", "subscribe_scan", "unsubscribe")


@builtin_handlers(matcher=subscribe_matcher)
def subscribe(message, request, *args, **kwargs):
    """处理关注与取消关注"""
    # 关注事件
    if message.event in ("subscribe", "subscribe_scan"):
        # 首次订阅
        subscribed = request.user.ext_info.get("subscribed", None)
        request.user.first_subscribe = subscribed is None
        request.user.ext_info["subscribed"] = True
        request.user.ext_info["latest_subscribe_time"] = int(time.time())
        request.user.save()

    # 取关事件
    if message.event == "unsubscribe":
        request.user.ext_info["subscribed"] = False
        request.user.ext_info["latest_unsubscribe_time"] = int(time.time())
        request.user.save()


def thirdpartyplatform_ticket_matcher(message, request, *args, **kwargs):
    return request.wechat_app.type == AppType.THIRDPARTYPLATFORM\
           and message.type == "component_verify_ticket"


@builtin_handlers(matcher=thirdpartyplatform_ticket_matcher)
def thirdpartyplatform_ticket(message, request, *args, **kwargs):
    """接收第三方平台ticket"""
    request.wechat_app.session.set("component_verify_ticket",
                                   message.verify_ticket)
    return PlainTextReply("success")


def thirdpartyplatform_authorize_matcher(message, request, *args, **kwargs):
    return request.wechat_app.type == AppType.THIRDPARTYPLATFORM\
           and message.type in ("authorized", "updateauthorized")


@builtin_handlers(matcher=thirdpartyplatform_authorize_matcher)
def thirdpartyplatform_authorize(message, request, *args, **kwargs):
    """接收第三方平台授权变更"""
    request.wechat_app.query_auth(message.authorization_code)
    return PlainTextReply("success")


def thirdpartyplatform_unauthorize_matcher(message, request, *args, **kwargs):
    return request.wechat_app.type == AppType.THIRDPARTYPLATFORM\
           and message.type == "unauthorized"


@builtin_handlers(matcher=thirdpartyplatform_unauthorize_matcher)
def thirdpartyplatform_unauthorize(message, request, *args, **kwargs):
    """第三方平台取消授权"""
    app = request.wechat_app.children.get(appid=message.authorizer_appid)
    del app._access_token
    del app.refresh_token
    return PlainTextReply("success")
