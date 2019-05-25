# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class AppType(object):
    OTHER = 0
    SERVICEAPP = 1
    SUBSCRIBEAPP = 2
    MINIPROGRAM = 4


class MsgType(object):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"


class MsgLogFlag(object):
    LOG_MESSAGE = 0x01
    LOG_REPLY = 0x02
