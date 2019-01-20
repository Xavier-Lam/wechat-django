import datetime
from hashlib import md5
import json

from django.db import models as m, transaction
from django.utils.translation import ugettext as _
from jsonfield import JSONField

from . import MessageHandler, ReplyMsgType, WechatApp
from .. import utils

class Menu(m.Model):
    class Event(object):
        CLICK = "click"
        VIEW = "view"
        # SCANCODEPUSH = "scancode_push"
        # SCANCODEWAITMSG = "scancode_waitmsg"
        # PICSYSPHOTO = "pic_sysphoto"
        # PICPHOTOORALBUM = "pic_photo_or_album"
        # PICWEIXIN = "pic_weixin"
        # LOCATIONSELECT = "location_select"
        # MEDIAID = "media_id"
        # VIEWLIMITED = "view_limited"

        MINIPROGRAM = "miniprogram"

    app = m.ForeignKey(WechatApp, on_delete=m.CASCADE,
        related_name="menus")
    name = m.CharField(_("name"), max_length=16)
    menuid = m.IntegerField(_("menuid"), null=True, blank=True)
    parent = m.ForeignKey("Menu", on_delete=m.CASCADE,
        null=True, blank=True, related_name="sub_button")
    type = m.CharField(_("type"), max_length=20, choices=utils.enum2choices(Event),
        null=True, blank=True)
    content = JSONField()

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created = m.DateTimeField(auto_now_add=True)
    updated = m.DateTimeField(auto_now=True)

    class Meta(object):
        ordering = ("app", "-weight", "created")

    @staticmethod
    def sync(app):
        """
        :type app: .WeChatApp
        """
        resp = app.client.menu.get_menu_info()
        
        # 旧menu 旧handler
        with transaction.atomic():
            app.menus.all().delete()
            # 移除同步菜单产生的message handler
            app.message_handlers.filter(src=MessageHandler.Source.MENU).delete()
            return [Menu.mp2menu(menu, app) for menu in resp["selfmenu_info"]["button"]]

    @classmethod
    def mp2menu(cls, data, app):
        """
        :type app: .WeChatApp
        """
        menu = cls(name=data["name"], app=app)
        menu.type = data.get("type")
        if not menu.type:
            menu.save()
            menu.sub_button.add(*[
                cls.mp2menu(sub, app) for sub in 
                (data.get("sub_button") or dict(list=[])).get("list")
            ])
        elif menu.type in (cls.Event.VIEW, cls.Event.CLICK, 
            cls.Event.MINIPROGRAM):
            menu.content = data
        else:
            # 要当作回复处理了
            menu.type = cls.Event.CLICK
            # 生成一个唯一key
            key = md5(json.dumps(data).encode()).hexdigest()
            menu.content = dict(key=key)
            handler = MessageHandler.from_menu(menu, data, app)
        menu.save()
        return menu

    @staticmethod
    def upload(app):
        """
        :type app: .WeChatApp
        """
        data = dict(
            button=[menu.to_json() for menu in app.menus]
        )
        resp = app.client.menu.create(data)
        if resp["errcode"] == 0:
            pass

    def to_json(self):
        rv = dict(name=self.name)
        if self.type:
            if self.type == Menu.Event.CLICK:
                rv["key"] = self.content
            elif self.type == Menu.Event.VIEW:
                rv["url"] = self.content
            elif self.type == Menu.Event.MINIPROGRAM:
                rv["url"] = self.content
                rv.update(**self.ext_info)
            else:
                # TODO: 不存在类型
                raise Exception()
        else:
            rv["sub_button"] = [button.to_json() for button in self.sub_button]
        return rv

    def __str__(self):
        return self.name