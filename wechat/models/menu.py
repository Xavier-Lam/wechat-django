import datetime
from hashlib import md5
import json

from django.db import models, transaction
from jsonfield import JSONField

from . import MessageHandler, ReplyMsgType, WechatApp

class Menu(models.Model):
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

    app = models.ForeignKey(WechatApp, on_delete=models.CASCADE,
        related_name="menus")
    name = models.CharField(max_length=16)
    menuid = models.IntegerField(null=True)
    pid = models.ForeignKey("Menu", on_delete=models.CASCADE,
        null=True, related_name="sub_button")
    type = models.CharField(max_length=20)
    content = JSONField()
    ext_info = JSONField()

    weight = models.IntegerField(default=0, null=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    @staticmethod
    def sync(app):
        """
        :type app: .WeChatApp
        """
        resp = app.client.menu.get_menu_info()
        menus = [Menu.mp2menu(menu) for menu in resp["selfmenu_info"]["button"]]
        
        # 旧menu 旧handler
        with transaction.atomic():
            app.menus.delete()
            app.message_handlers.filter(
                src=MessageHandler.Source.MENU
            ).delete()

    @staticmethod
    def mp2menu(data, app):
        """
        :type app: .WeChatApp
        """
        menu = Menu(name=data["name"], app=app)
        menu.raw = data
        menu.type = data.get("type")
        if not menu.type:
            pass
        elif menu.type == Menu.Event.VIEW:
            menu.content = data["url"]
        elif menu.type == Menu.Event.CLICK:
            menu.content = data["key"]
        elif menu.type == Menu.Event.MINIPROGRAM:
            menu.content = data["url"]
            menu.ext_info = dict(
                appid=data["appid"],
                pagepath=data["pagepath"]
            )
        else:
            # 要当作回复处理了
            menu.type = Menu.Event.CLICK
            menu.content = md5(json.dumps(self.raw).encode()).hexdigest()
            handler = MessageHandler.from_menu(menu, data, app)
        menu.sub_button = [mp2menu(sub) for sub in data.get("sub_button") or []]
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