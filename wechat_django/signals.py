from sys import intern

from django.dispatch import Signal

from wechat_django.models import Application


def _fix_sender(sender):
    if isinstance(sender, Application):
        sender = sender.name
    return sender and intern(sender)


class WeChatDjangoSignal(Signal):
    def connect(self, receiver, sender=None, weak=True, dispatch_uid=None):
        sender = _fix_sender(sender)
        return super().connect(receiver, sender=sender, weak=weak,
                               dispatch_uid=dispatch_uid)

    def disconnect(self, receiver=None, sender=None, dispatch_uid=None):
        sender = _fix_sender(sender)
        return super().disconnect(receiver=receiver, sender=sender,
                                  dispatch_uid=dispatch_uid)

    def has_listeners(self, sender=None):
        sender = _fix_sender(sender)
        return super().has_listeners(sender=sender)

    def send(self, sender, **named):
        if isinstance(sender, Application):
            named.setdefault("wechat_app", sender)
        sender = _fix_sender(sender)
        return super().send(sender, **named)

    def send_robust(self, sender, **named):
        if isinstance(sender, Application):
            named.setdefault("wechat_app", sender)
        sender = _fix_sender(sender)
        return super().send_robust(sender, **named)


message_received = WeChatDjangoSignal((
    "wechat_app", "message", "request"))
"""
The message handler received a message

``wechat_app``
    The :class:`~wechat_django.models.apps.Application` received the message

``message``
    The message received by handler, which is a
    :class:`~wechatpy.messages.BaseMessage` or a
    :class:`~wechatpy.component.BaseComponentMessage` instance

``request``
    The current :class:`~django.http.HttpRequest`
"""

message_replied = WeChatDjangoSignal((
    "wechat_app", "reply", "message", "response_content"))
"""
The message handler has replied a message to client

``wechat_app``
    The :class:`~wechat_django.models.apps.Application` received the message

``reply``
    The :class:`~wechatpy.replies.BaseReply` sent to client

``message``
    The message received by handler, which is a
    :class:`~wechatpy.messages.BaseMessage` or a
    :class:`~wechatpy.component.BaseComponentMessage` instance

``request``
    The current :class:`~django.http.HttpRequest`
"""

message_handle_failed = WeChatDjangoSignal((
    "wechat_app", "message", "exc", "request"))
"""
An error occurred when handling a message

``wechat_app``
    The :class:`~wechat_django.models.apps.Application` received the message

``message``
    The message received by handler, which is a
    :class:`~wechatpy.messages.BaseMessage` or a
    :class:`~wechatpy.component.BaseComponentMessage` instance

``exc``
    The raised exception

``request``
    The current :class:`~django.http.HttpRequest`
"""

message_sent = WeChatDjangoSignal(("wechat_app", "reply", "message"))
"""
The message handler has sent a message to client

``wechat_app``
    The :class:`~wechat_django.models.apps.Application` received the message

``reply``
    The :class:`~wechatpy.replies.BaseReply` sent to client by calling custom
    message api

``message``
    The message received by handler, which is a
    :class:`~wechatpy.messages.BaseMessage` or a
    :class:`~wechatpy.component.BaseComponentMessage` instance
"""

message_send_failed = WeChatDjangoSignal((
    "wechat_app", "reply", "message", "exc", "request"))
"""
An error occurred when sending a message

``wechat_app``
    The :class:`~wechat_django.models.apps.Application` received the message

``reply``
    The :class:`~wechatpy.replies.BaseReply` sent to client by calling custom
    message api

``message``
    The message received by handler, which is a
    :class:`~wechatpy.messages.BaseMessage` or a
    :class:`~wechatpy.component.BaseComponentMessage` instance

``exc``
    The raised exception

``request``
    The current :class:`~django.http.HttpRequest`
"""


post_oauth = WeChatDjangoSignal((
    "wechat_app", "user", "scope", "state", "request"))
"""
Webpage authorize successfully

``wechat_app``
    The :class:`~wechat_django.models.apps.Application` instance

``user``
    The :class:`~wechat_django.models.User` who granted permissions to us

``scope``
    OAuth2 scope `tuple`

``state``
    OAuth2 state

``request``
    The current :class:`~django.http.HttpRequest`
"""
