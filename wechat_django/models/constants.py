# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class MsgType(object):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"


class MsgLogFlag(object):
    LOG_MESSAGE = 0x01
    LOG_REPLY = 0x02
