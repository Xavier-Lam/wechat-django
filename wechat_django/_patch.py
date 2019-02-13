#encoding: utf-8
import time
from wechatpy import replies
from wechatpy.fields import *
from wechatpy.replies import EmptyReply, REPLY_TYPES

import xmltodict


def deserialize_reply(xml, update_time=False):
    """反序列化被动回复
    :param xml: 待反序列化的xml
    :param update_time: 是否用当前时间替换xml中的时间
    :raises ValueError: 不能辨识的reply xml
    :rtype: wechatpy.replies.BaseReply
    """
    if not xml:
        return EmptyReply()

    try:
        reply_dict = xmltodict.parse(xml)["xml"]
        msg_type = reply_dict["MsgType"]
    except:
        raise ValueError("bad reply xml")
    if msg_type not in REPLY_TYPES:
        raise ValueError("unknown reply type")

    cls = REPLY_TYPES[msg_type]
    kwargs = dict()
    for attr, field in cls._fields.items():
        if field.name in reply_dict:
            str_value = reply_dict[field.name]
            kwargs[attr] = field.from_xml(str_value)

    if update_time:
        kwargs["time"] = time.time()

    return cls(**kwargs)

replies.deserialize_reply = deserialize_reply


def from_xml(cls, value):
    return value
BaseField.from_xml = classmethod(from_xml)


def from_xml_media_id(cls, value):
    return value["MediaId"]
ImageField.from_xml = classmethod(from_xml_media_id)
VoiceField.from_xml = classmethod(from_xml_media_id)


def from_xml_video(cls, value):
    return dict(
        media_id=value["MediaId"],
        title=value.get("Title"),
        description=value.get("Description")
    )
VideoField.from_xml = classmethod(from_xml_video)


def from_xml_music(cls, value):
    return dict(
        thumb_media_id=value["ThumbMediaId"],
        title=value.get("Title"),
        description=value.get("Description"),
        music_url=value.get("MusicUrl"),
        hq_music_url=value.get("HQMusicUrl")
    )
MusicField.from_xml = classmethod(from_xml_music)


def from_xml_articles(cls, value):
    return [dict(
        title=item["Title"],
        description=item["Description"],
        image=item["PicUrl"],
        url=item["Url"]
    ) for item in value["item"]]
ArticlesField.from_xml = classmethod(from_xml_articles)
