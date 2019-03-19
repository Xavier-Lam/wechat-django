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
from django.views import View
import six
from wechatpy import replies
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature
import xmltodict

from . import settings
from .exceptions import BadMessageRequest, MessageHandleError
from .models import MessageHandler, MessageLog, WeChatMessageInfo
from .sites.wechat import patch_request

__all__ = ("handler", "Handler", "message_handler")


class Handler(View):
    def dispatch(self, request):
        """
        :type request: wechat_django.requests.WeChatMessageRequest
        """
        if not request.wechat.app.abilities.interactable:
            return response.HttpResponseNotFound()
        log = MessageHandler.handlerlog(request)
        try:
            self._verify(request)
            resp = super(Handler, self).dispatch(request)
            if not isinstance(resp, response.HttpResponseNotFound):
                log(logging.DEBUG, "receive a message")
            return resp
        except MultiValueDictKeyError:
            log(logging.WARNING, "bad request args", exc_info=True)
            return response.HttpResponseBadRequest()
        except BadMessageRequest:
            log(logging.WARNING, "bad request", exc_info=True)
            return response.HttpResponseBadRequest()
        except InvalidSignatureException:
            log(logging.WARNING, "invalid signature", exc_info=True)
            return response.HttpResponseBadRequest()
        except xmltodict.expat.ExpatError:
            log(logging.WARNING, "deserialize message failed", exc_info=True)
            return response.HttpResponseBadRequest()
        except MessageHandleError:
            log(logging.WARNING, "handle message failed", exc_info=True)
            return ""
        except:
            log(logging.ERROR, "an unexcepted error occurred", exc_info=True)
            return ""

    def get(self, request):
        return request.GET["echostr"]

    def post(self, request):
        request = patch_request(request, cls=WeChatMessageInfo)
        reply = self._handle(request.wechat)
        if reply:
            xml = reply.render()
            if request.wechat.app.crypto:
                xml = request.wechat.app.crypto.encrypt_message(
                    xml, request.GET["nonce"], request.GET["timestamp"])
            return response.HttpResponse(xml, content_type="text/xml")
        return ""

    def _verify(self, request):
        """检验请求"""
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


def message_handler(names_or_func=None):
    """自定义回复业务需加装该装饰器
    被装饰的自定义业务接收一个``wechat_django.models.WeChatMessageInfo``对象
    并且返回一个``wechatpy.replies.BaseReply``对象

    :param names_or_func: 允许使用该message_handler的appname 不填所有均允许
    :type names_or_func: str or list or tuple or callable

        @message_handler
        def custom_business(message):
            user = message.user
            # ...
            return TextReply("hello", message=message.message)

        @message_handler(("app_a", "app_b"))
        def app_ab_only_business(message):
            # ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def decorated_view(message):
            return view_func(message)
        decorated_view.message_handler = names or True

        return decorated_view

    if isinstance(names_or_func, six.text_type):
        names = [names_or_func]
    elif callable(names_or_func):
        names = None
        return decorator(names_or_func)

    return decorator


handler = Handler.as_view()
