from django.utils.functional import SimpleLazyObject

from .base import MessageHandlerCollection


message_handlers = SimpleLazyObject(MessageHandlerCollection)  # type: MessageHandlerCollection  # noqa
"""The default message handler, it can counter most cases."""
