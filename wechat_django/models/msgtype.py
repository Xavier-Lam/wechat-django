# -*- coding: utf-8 -*-
from __future__ import unicode_literals

class MsgType(object):
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"


class ReceiveMsgType(MsgType):
    LOCATION = "location"
    LINK = "link"
    SHORTVIDEO = "shortvideo"
    EVENT = "event"


class EventType(object):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SCAN = "SCAN"
    LOCATION = "LOCATION"
    CLICK = "CLICK"
    VIEW = "VIEW"
