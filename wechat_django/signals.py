from sys import intern

from django.dispatch import Signal

from wechat_django.models.apps.base import Application


def _fix_sender(sender):
    from wechat_django.models import Application
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
message_replied = WeChatDjangoSignal((
    "wechat_app", "reply", "message", "response_content"))
message_handle_failed = WeChatDjangoSignal((
    "wechat_app", "message", "exc", "request"))
message_sent = WeChatDjangoSignal(("wechat_app", "reply", "message"))
message_send_failed = WeChatDjangoSignal((
    "wechat_app", "reply", "message", "exc", "request"))
