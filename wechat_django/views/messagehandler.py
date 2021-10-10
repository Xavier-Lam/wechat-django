from contextlib import contextmanager
import time

from django.core.cache import cache
from django.http import response
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext_lazy as _
from wechatpy.exceptions import InvalidSignatureException
from wechatpy.utils import check_signature
import xmltodict

from wechat_django import signals
from wechat_django.authentication import MessageHandlerAuth
from wechat_django.core.view import WeChatView
from wechat_django.exceptions import BadMessageRequest
from wechat_django.models.apps.mixins import MessagePushApplicationMixin
from wechat_django.models.apps.thirdpartyplatform import (
    AuthorizerApplication, ThirdPartyPlatform)
from wechat_django.sites import default_site
from wechat_django.messagehandler import (
    builtin_handlers, message_handlers,  MessageHandlerCollection)


class MessageResponse(response.HttpResponse):
    def __init__(self, request, replies, *args, **kwargs):
        self._request = request
        self.replies = replies
        kwargs["content_type"] = "text/xml"
        super().__init__(b'', *args, **kwargs)

    def close(self):
        wechat_app = self._request.wechat_app
        signals.message_replied.send_robust(wechat_app,
                                            reply=self.replies[0],
                                            message=self._request.message,
                                            response_content=self.content)

        # 主动发送消息
        for reply in self.replies[1:]:
            try:
                wechat_app.send_message(reply)
                signals.message_sent.send_robust(
                    wechat_app, reply=reply, message=self._request.message)
            except Exception as e:
                wechat_app.logger("messagehandler").exception(
                    _("An exception occurred when sending message"), extra={
                        "url": self._request.get_full_path(),
                        "body": self._request.body
                    })
                signals.message_send_failed.send_robust(
                    wechat_app, reply=reply, message=self._request.message,
                    exc=e, request=self._request)

        return super().close()

    @property
    def content(self):
        if not hasattr(self, "_content"):
            self._content = b""
            if self.replies:
                self._content = self._request.wechat_app.encrypt_message(
                    self.replies[0], self._request).encode()
        return self._content

    @content.setter
    def content(self, value):
        pass


@default_site.register
class Handler(WeChatView):
    DEFAULT_OFFSET = 600

    authentication_classes = (MessageHandlerAuth,)

    include_application_classes = (MessagePushApplicationMixin,
                                   AuthorizerApplication)
    url_pattern = r"^notify/$"
    url_name = "handler"

    def initial(self, request, *args, **kwargs):
        try:
            timestamp = int(request.GET["timestamp"])
        except ValueError:
            raise BadMessageRequest(_("Invalid timestamp"))
        sign = request.GET["signature"]
        nonce = request.GET["nonce"]

        # 检查timestamp
        time_diff = int(timestamp) - time.time()
        if abs(time_diff) > self.DEFAULT_OFFSET:
            raise BadMessageRequest(_("Invalid time"))

        # 防重放检查及签名检查
        with self.check_nonce(request.wechat_app, sign, nonce, time_diff):
            check_signature(
                request.wechat_app.crypto.token,
                sign,
                timestamp,
                nonce
            )

        if request.method == "POST":
            request.message = self.parse_message(request, *args, **kwargs)
            signals.message_received.send_robust(request.wechat_app,
                                                 message=request.message,
                                                 request=request)

        super().initial(request, *args, **kwargs)

    def handle_exception(self, exc):
        if isinstance(exc, (response.Http404,)):
            return super().handle_exception(exc)
        if isinstance(exc, (MultiValueDictKeyError, BadMessageRequest,
                            InvalidSignatureException,
                            xmltodict.expat.ExpatError)):
            self.request.wechat_app.logger("messagehandler").warning(
                _("Received an unexpected request"),
                extra={
                    "url": self.request.get_full_path(),
                    "body": self.request.body
                }
            )
            return response.HttpResponseBadRequest()
        # 用户抛出的异常,返回空响应
        return ""

    def get(self, request, *args, **kwargs):
        return request.GET["echostr"]

    def post(self, request, *args, **kwargs):
        try:
            replies = self.handle_message(
                request.message, request, *args, **kwargs)
        except Exception as e:
            request.wechat_app.logger("messagehandler").exception(
                _("An exception occurred when handling message"), extra={
                    "url": request.get_full_path(),
                    "body": request.body
                })
            signals.message_handle_failed.send_robust(
                request.wechat_app, message=request.message, exc=e,
                request=request)
            raise

        return self.make_response(replies, request, *args, **kwargs)

    @contextmanager
    def check_nonce(self, wechat_app, sign, nonce, time_diff):
        """nonce防重放"""
        nonce_key = "wechat_django:{name}:{sign}".format(name=wechat_app.name,
                                                         sign=sign)
        if cache.get(nonce_key) == nonce:
            raise BadMessageRequest(_("Repeat nonce string"))
        try:
            yield
            expires = self.DEFAULT_OFFSET + time_diff
            cache.set(nonce_key, nonce, expires)
        finally:
            pass

    def parse_message(self, request, *args, **kwargs):
        app = request.wechat_app
        raw_message = app.decrypt_message(request)
        return app.parse_message(raw_message)

    def handle_message(self, message, request, *args, **kwargs):
        """处理消息"""
        handlers = MessageHandlerCollection(message_handlers, builtin_handlers)
        return handlers.handle(message, request, *args, **kwargs)

    def make_response(self, replies, request, *args, **kwargs):
        return MessageResponse(request, replies)


class AuthorizerHandler(Handler):
    required_application_classes = (AuthorizerApplication,)
    url_pattern = r"^notify/(?P<appid>[-_a-zA-Z\d\$]+)/?$"
    url_name = "authorizer_handler"

    def get_app(self, request, *args, **kwargs):
        if not hasattr(request, "wechat_app"):
            # 该地址注册在第三方平台上,app需转换为托管app
            platform_name = super().get_app_name(request, *args, **kwargs)
            platform = ThirdPartyPlatform.objects.get(name=platform_name)
            request.wechat_app = platform.children.get(appid=kwargs["appid"])
        return request.wechat_app

    def get_app_name(self, request, *args, **kwargs):
        return self.get_app(request, *args, **kwargs).name
