# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import md5
import json

from django.db import models as m, transaction
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from ..utils.model import enum2choices
from . import appmethod, MessageHandler, WeChatApp, WeChatModel


class MenuManager(m.Manager):
    def get_queryset(self):
        return (super(MenuManager, self).get_queryset()
            .prefetch_related("sub_button"))


class Menu(WeChatModel):
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

    app = m.ForeignKey(
        WeChatApp, related_name="menus", on_delete=m.CASCADE)
    name = m.CharField(_("name"), max_length=16)
    menuid = m.IntegerField(_("menuid"), null=True, blank=True)
    parent = m.ForeignKey(
        "Menu", related_name="sub_button", null=True, blank=True,
        on_delete=m.CASCADE)
    type = m.CharField(
        _("type"), max_length=20, choices=enum2choices(Event),
        null=True, blank=True)
    content = JSONField()

    weight = m.IntegerField(_("weight"), default=0, null=False)
    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    class Meta(object):
        verbose_name = _("menu")
        verbose_name_plural = _("menus")

        ordering = ("app", "-weight", "id")

    objects = MenuManager()

    @appmethod("sync_menus")
    def sync(cls, app):
        """
        从微信同步菜单数据
        :type app: wechat_django.models.WeChatApp
        """
        resp = app.client.menu.get_menu_info()
        try:
            data = resp["selfmenu_info"]["button"]
        except KeyError:
            data = []

        with transaction.atomic():
            # 旧menu
            app.menus.all().delete()
            # 移除同步菜单产生的message handler
            app.message_handlers.filter(
                src=MessageHandler.Source.MENU).delete()
            rv = [cls.json2menu(menu, app) for menu in data]
        app.ext_info["current_menus"] = cls.menus2json(app)
        app.save()
        return rv

    @appmethod("publish_menus")
    def publish(cls, app, menuid=None):
        """
        发布菜单
        :type app: wechat_django.models.WeChatApp
        """
        data = cls.menus2json(app, menuid)
        rv = app.client.menu.create(data)
        app.ext_info["current_menus"] = data
        app.save()
        return rv

    @classmethod
    def get_menus(cls, app, menuid=None):
        """获取数据库中公众号菜单配置"""
        q = app.menus.filter(parent_id__isnull=True)
        q = q.filter(menuid=menuid) if menuid else q.filter(menuid__isnull=True)
        return list(q.all())

    @classmethod
    def menus2json(cls, app, menuid=None):
        menus = cls.get_menus(app, menuid)
        return dict(button=[menu.to_json() for menu in menus])

    @classmethod
    def json2menu(cls, data, app):
        """
        :type app: wechat_django.models.WeChatApp
        """
        menu = cls(name=data["name"], app=app)
        menu.type = data.get("type")
        if not menu.type:
            menu.save()
            menu.sub_button.add(*[
                cls.json2menu(sub, app) for sub in
                (data.get("sub_button") or dict(list=[])).get("list")
            ])
        elif menu.type in (
            cls.Event.VIEW, cls.Event.CLICK, cls.Event.MINIPROGRAM):
            menu.content = data
        else:
            # 要当作回复处理了
            menu.type = cls.Event.CLICK
            # 生成一个唯一key
            key = md5(json.dumps(data).encode()).hexdigest()
            menu.content = dict(key=key)
            MessageHandler.from_menu(menu, data)
        menu.save()
        return menu

    def to_json(self):
        rv = dict(name=self.name)
        if self.type:
            rv["type"] = self.type
            if self.type in (Menu.Event.CLICK, Menu.Event.VIEW,
                Menu.Event.MINIPROGRAM):
                rv.update(self.content)
            else:
                raise ValueError("incorrect menu type")
        else:
            rv["sub_button"] = [btn.to_json() for btn in self.sub_button.all()]
        return rv

    def __str__(self):
        return "{0}".format(self.name)
