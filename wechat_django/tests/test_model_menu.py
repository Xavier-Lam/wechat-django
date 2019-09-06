# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechatpy.client.api import WeChatMenu

from ..models import Material, Menu, WeChatApp
from .base import mock, WeChatTestCase


class MenuTestCase(WeChatTestCase):
    def test_sync(self):
        """测试同步菜单"""
        permenant_media = "permenant_media_id"

        app = self.app

        # 微信官方菜单
        data = self.load_data("mp_menu_data")
        buttons = data["selfmenu_info"]["button"]
        with mock.patch.object(WeChatApp, "as_permenant_material"),\
            mock.patch.object(WeChatApp, "sync_articles"),\
            mock.patch.object(WeChatMenu, "get_menu_info"):

            WeChatApp.as_permenant_material.return_value = permenant_media
            WeChatApp.sync_articles.return_value = None
            WeChatMenu.get_menu_info.return_value = data

            app.sync_menus()
            self.assertMenusEqual(self.menus, buttons)

        # 微信菜单不存在
        data = {
            "is_menu_open": 0
        }
        with mock.patch.object(WeChatMenu, "get_menu_info"):
            WeChatMenu.get_menu_info.return_value = data

            Menu.sync(app)
            self.assertEqual(self.menus.count(), 0)

        # 同步自定义菜单
        data = self.load_data("self_menu_data")
        buttons = data["selfmenu_info"]["button"]
        with mock.patch.object(WeChatMenu, "get_menu_info"):
            WeChatMenu.get_menu_info.return_value = data

            Menu.sync(app)
            self.assertMenusEqual(self.menus, buttons)

    def test_menu_publish(self):
        # 菜单发布
        pass

    def assertMenusEqual(self, menus, buttons):
        self.assertEqual(len(menus), len(buttons))
        for menu, button in zip(menus, buttons):
            self.assertMenuEqual(menu, button)

    def assertMenuEqual(self, menu, button):
        self.assertEqual(menu.name, button["name"])
        if "sub_button" in button:
            self.assertIsNone(menu.type)
            sub_menus = menu.sub_button.all()
            sub_buttons = button["sub_button"]["list"]
            self.assertMenusEqual(sub_menus, sub_buttons)
        elif button["type"] == Menu.Event.CLICK:
            self.assertEqual(menu.type, button["type"])
            self.assertEqual(menu.content["key"], button["key"])
        elif button["type"] == Menu.Event.VIEW:
            self.assertEqual(menu.type, button["type"])
            self.assertEqual(menu.content["url"], button["url"])
        else:
            # 回复转换为handler
            pass

    @property
    def menus(self):
        return (self.app.menus.filter(menuid__isnull=True)
            .filter(parent_id__isnull=True)
            .all())
