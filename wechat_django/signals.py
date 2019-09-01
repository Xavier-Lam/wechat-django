# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.dispatch import Signal


message_received = Signal(["message_info"])
"""收到微信推送消息"""

message_handled = Signal(["message_info", "reply"])
"""微信推送消息处理成功(不包括成功)"""

message_error = Signal(["message_info", "exc"])
"""微信推送消息处理异常"""
