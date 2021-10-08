from sys import intern

from django.dispatch import Signal


class WeChatDjangoSignal(Signal):
    def connect(self, receiver, sender=None, weak=True, dispatch_uid=None):
        sender = sender and intern(sender)
        return super().connect(receiver, sender=sender, weak=weak,
                               dispatch_uid=dispatch_uid)

    def disconnect(self, receiver=None, sender=None, dispatch_uid=None):
        sender = sender and intern(sender)
        return super().disconnect(receiver=receiver, sender=sender,
                                  dispatch_uid=dispatch_uid)

    def has_listeners(self, sender=None):
        sender = sender and intern(sender)
        return super().has_listeners(sender=sender)

    def send(self, sender, **named):
        sender = intern(sender)
        return super().send(sender, **named)

    def send_robust(self, sender, **named):
        sender = intern(sender)
        return super().send_robust(sender, **named)
