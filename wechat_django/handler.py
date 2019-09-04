# -*- coding: utf-8 -*-

"""微信消息处理器"""

from __future__ import unicode_literals

from contextlib import contextmanager
from functools import wraps
import logging
import time

from django.core.cache import cache
from django.http import response
from django.utils.datastructures import MultiValueDictKeyError
import six
from wechatpy import replies
from wechatpy.events import BaseEvent
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature
import xmltodict

from . import settings, signals
from .exceptions import BadMessageRequest, MessageHandleError
from .sites.wechat import default_site, WeChatView

__all__ = ("handle_subscribe_events", "Handler", "message_handler",
           "message_rule")


@default_site.register
class Handler(WeChatView):
    url_pattern = r"^$"
    url_name = "handler"

    def initial(self, request, appname):
        try:
            timestamp = int(request.GET["timestamp"])
        except ValueError:
            raise BadMessageRequest("invalid timestamp")
        sign = request.GET["signature"]
        nonce = request.GET["nonce"]

        time_diff = int(timestamp) - time.time()
        # 检查timestamp
        if abs(time_diff) > settings.MESSAGETIMEOFFSET:
            raise BadMessageRequest("invalid time")

        # 防重放检查及签名检查
        with self._no_repeat_nonces(sign, nonce, time_diff):
            check_signature(
                request.wechat.app.token,
                sign,
                timestamp,
                nonce
            )

    def finalize_response(self, request, resp, *args, **kwargs):
        if not isinstance(resp, response.HttpResponseNotFound):
            self.log(logging.DEBUG, "receive a message")
        return super(Handler, self).finalize_response(
            request, resp, *args, **kwargs)

    def handle_exception(self, exc):
        if isinstance(exc, MultiValueDictKeyError):
            self.log(logging.WARNING, "bad request args", exc_info=True)
            return response.HttpResponseBadRequest()
        elif isinstance(exc, BadMessageRequest):
            self.log(logging.WARNING, "bad request", exc_info=True)
            return response.HttpResponseBadRequest()
        elif isinstance(exc, InvalidSignatureException):
            self.log(logging.WARNING, "invalid signature", exc_info=True)
            return response.HttpResponseBadRequest()
        elif isinstance(exc, xmltodict.expat.ExpatError):
            self.log(logging.WARNING, "deserialize message failed",
                     exc_info=True)
            return response.HttpResponseBadRequest()
        elif isinstance(exc, MessageHandleError):
            self.log(logging.WARNING, "handle message failed", exc_info=True)
            return ""
        else:
            self.log(logging.ERROR, "an unexcepted error occurred",
                     exc_info=True)
            return ""

    def get(self, request, appname):
        return request.GET["echostr"]

    def post(self, request, appname):
        message_info = request.wechat
        signals.message_received.send(request.wechat.app.staticname,
                                      message_info=message_info)
        try:
            reply = self._handle(message_info)
            signals.message_handled.send(request.wechat.app.staticname,
                                         message_info=message_info,
                                         reply=reply)
            if reply:
                xml = reply.render()
                if request.wechat.app.crypto:
                    xml = request.wechat.app.crypto.encrypt_message(
                        xml, request.GET["nonce"], request.GET["timestamp"])
                return response.HttpResponse(xml, content_type="text/xml")
        except Exception as exc:
            signals.message_error.send(request.wechat.app.staticname,
                                       message_info=message_info, exc=exc)
            raise
        return ""

    def _update_wechat_info(self, request, *args, **kwargs):
        from .models import WeChatMessageInfo
        return WeChatMessageInfo.from_wechat_info(request.wechat)

    @contextmanager
    def _no_repeat_nonces(self, sign, nonce, time_diff):
        """nonce防重放"""
        nonce_key = "wx:m:n:{0}".format(sign)
        if settings.MESSAGENOREPEATNONCE:
            if cache.get(nonce_key) == nonce:
                raise BadMessageRequest("repeat nonce string")
            try:
                yield
                expires = settings.MESSAGETIMEOFFSET + time_diff
                cache.set(nonce_key, nonce, expires)
            finally:
                pass
        else:
            yield

    def _handle(self, message_info):
        """处理消息"""
        from .models import MessageHandler, MessageLog

        handlers = MessageHandler.matches(message_info)
        if not handlers:
            return None

        handler = handlers[0]
        reply = handler.reply(message_info)
        if handler.log_message or message_info.app.log_message:
            MessageLog.from_message_info(message_info)
        if not reply or isinstance(reply, replies.EmptyReply):
            return None
        return reply

    _log = None

    @property
    def log(self):
        if not self._log:
            from .models import MessageHandler
            self._log = MessageHandler.handlerlog(self.request)
        return self._log


def message_handler(names_or_func=None):
    """
    自定义回复业务需加装该装饰器
    被装饰的自定义业务接收一个``wechat_django.models.WeChatMessageInfo``对象
    并且返回一个``wechatpy.replies.BaseReply``对象

    :param names_or_func: 允许使用该message_handler的appname 不填所有均允许
    :type names_or_func: str or list or tuple or callable

        @message_handler
        def custom_business(message):
            user = message.user
            # ...
            return TextReply("hello")

        @message_handler(("app_a", "app_b"))
        def app_ab_only_business(message):
            # ...
    """
    return _decorator("message_handler", names_or_func)


def message_rule(names_or_func=None):
    """
    自定义规则需加装该装饰器
    接收一个`wechat_django.models.WeChatMessageInfo`对象
    返回一个bool值,真值则表示规则符合

        @message_rule
        def custom_rule(message_info):
            user = message.user
            # ...
            return True

        @message_rule(("app_a", "app_b"))
        def app_ab_only_rule(message):
            # ...
    """
    return _decorator("message_rule", names_or_func)


def _decorator(property, names_or_func):
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(message):
            return view_func(message)
        setattr(decorated_view, property, names or True)

        return decorated_view

    if isinstance(names_or_func, six.text_type):
        names = [names_or_func]
    elif callable(names_or_func):
        names = None
        return decorator(names_or_func)

    return decorator


def handle_subscribe_events(sender, message_info, **kwargs):
    """处理关注,取关"""
    message = message_info.message
    if isinstance(message, BaseEvent):
        # 关注事件
        if message.event in ("subscribe", "subscribe_scan"):
            message_info.local_user.subscribe = True
            message_info.local_user.subscribe_time = time.time()
            message_info.local_user.save()

        # 取关事件
        if message.event == "unsubscribe":
            message_info.local_user.subscribe = False
            message_info.local_user.save()
