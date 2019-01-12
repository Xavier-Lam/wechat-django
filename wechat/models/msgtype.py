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

class ReplyMsgType(MsgType):# 响应
    MUSIC = "music"
    NEWS = "news"

    # 自定义业务
    CUSTOM = "custom"
    FORWARD = "forward" # 转发

class EventType(object):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SCAN = "SCAN"
    LOCATION = "LOCATION"
    CLICK = "CLICK"
    VIEW = "VIEW"