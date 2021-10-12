from django.utils.functional import SimpleLazyObject

from .base import MessageHandlerCollection


message_handlers = SimpleLazyObject(MessageHandlerCollection)
"""默认消息处理器,能满足绝大部分情况"""
