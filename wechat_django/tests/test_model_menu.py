# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechatpy.client.api import WeChatMenu

from ..models import Article, Material, Menu
from .base import mock, WeChatTestCase
from .interceptors import wechatapi, wechatapi_accesstoken


class MenuTestCase(WeChatTestCase):
    def test_sync(self, *args):
        """测试同步菜单"""
        permenant_media = "permenant_media_id"

        app = self.app

        # 微信官方菜单
        data = self.mp_menu_data
        buttons = data["selfmenu_info"]["button"]
        with mock.patch.object(Material, "as_permenant"),\
            mock.patch.object(Article, "sync"),\
            mock.patch.object(WeChatMenu, "get_menu_info"):

            Material.as_permenant.return_value = permenant_media
            Article.sync.return_value = None
            WeChatMenu.get_menu_info.return_value = data

            Menu.sync(app)
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
        data = self.self_menu_data
        buttons = data["selfmenu_info"]["button"]
        with mock.patch.object(WeChatMenu, "get_menu_info"):
            WeChatMenu.get_menu_info.return_value = data

            Menu.sync(app)
            self.assertMenusEqual(self.menus, buttons)

    @property
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

    #region data
    @property
    def mp_menu_data(self):
        return {
            "is_menu_open": 1,
            "selfmenu_info": {
                "button": [
                    {
                        "type": "news",
                        "name": "菜单1tw",
                        "value": "Jfp2Vusaxl7ksvUU073PifoTrdighPHAlflIx5n6pwg",
                        "news_info": {
                            "list": [
                                {
                                    "title": "测试图文1标题",
                                    "author": "测试图文1作者",
                                    "digest": "测试图文1摘要",
                                    "show_cover": 0,
                                    "cover_url": "http://mmbiz.qpic.cn/mmbiz_jpg/wWibW2Saqk7fwakIgv3EuS6WA8W7duyjZ11Zia66QibD6D06LicoRPEPbshxe1y45iaO8OJEFAcwQzyB8wg1kDQ7gfw/0?wx_fmt=jpeg",
                                    "content_url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=1&sn=584bdd35d9053597a09b093ecf27fd35&chksm=7d6ee8864a196190f04d451fe7640d0c90fe17c06be6824980475c0b6fbb4e7f329b267e4452#rd",
                                    "source_url": "https://baidu.com"
                                },
                                {
                                    "title": "测试图文2标题",
                                    "author": "测试图文2作者",
                                    "digest": "测试图文2摘要",
                                    "show_cover": 0,
                                    "cover_url": "http://mmbiz.qpic.cn/mmbiz_jpg/wWibW2Saqk7fwakIgv3EuS6WA8W7duyjZDpdSVkibEFdJ5WApOQgL2c6m26eJpVOS4BEvFkBvl4CAfHzJAbYFQXw/0?wx_fmt=jpeg",
                                    "content_url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=2&sn=09ae15421414ed15270ae24b2fd1f7c2&chksm=7d6ee8864a1961900e4b1ee9122ab6ee5a6f9887d4d032e4afff440ecd19e6b894a5b45d86f6#rd",
                                    "source_url": ""
                                },
                                {
                                    "title": "无封面",
                                    "author": "",
                                    "digest": "大字小字",
                                    "show_cover": 0,
                                    "cover_url": "",
                                    "content_url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=3&sn=dbfdef0488b1a7edb7d096644b1519df&chksm=7d6ee8864a196190e84bf2e74eb62f9887f41dd1ccda4fa5d57a62e508ff5f57a02d1fd42154#rd",
                                    "source_url": ""
                                }
                            ]
                        }
                    },
                    {
                        "name": "菜单2",
                        "sub_button": {
                            "list": [
                                {
                                    "type": "view",
                                    "name": "菜单2跳转",
                                    "url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=1&sn=584bdd35d9053597a09b093ecf27fd35&chksm=7d6ee8864a196190f04d451fe7640d0c90fe17c06be6824980475c0b6fbb4e7f329b267e4452&scene=18#wechat_redirect"
                                },
                                {
                                    "type": "img",
                                    "name": "菜单2图片",
                                    "value": "xYeuFYP-2E4eDbS9qBClTbgaAiZevMfuHbtkUx6rmo0yJTwNo1pCclh4caLr64T9"
                                },
                                {
                                    "type": "voice",
                                    "name": "菜单2语音",
                                    "value": "BxYG4VDljZRmxbP-WCuPMZbS2YP6UY_bJrsgqtPI78GNNQYjAUPbbMZduc3SY9bh"
                                },
                                {
                                    "type": "video",
                                    "name": "菜单2视频",
                                    "value": "http://mp.weixin.qq.com/mp/mp/video?__biz=MzU3ODgxNDE4OA==&mid=100000002&sn=cfcded602f2178d88f39391f3b549a7d&vid=e1357pzft1c&idx=1&vidsn=7719378611189129ae93ae4a80fbf873&fromid=1#rd"
                                }
                            ]
                        }
                    },
                    {
                        "name": "菜单3",
                        "sub_button": {
                            "list": [
                                {
                                    "type": "news",
                                    "name": "菜单3图文",
                                    "value": "Jfp2Vusaxl7ksvUU073PifoTrdighPHAlflIx5n6pwg",
                                    "news_info": {
                                        "list": [
                                            {
                                                "title": "测试图文1标题",
                                                "author": "测试图文1作者",
                                                "digest": "测试图文1摘要",
                                                "show_cover": 0,
                                                "cover_url": "http://mmbiz.qpic.cn/mmbiz_jpg/wWibW2Saqk7fwakIgv3EuS6WA8W7duyjZ11Zia66QibD6D06LicoRPEPbshxe1y45iaO8OJEFAcwQzyB8wg1kDQ7gfw/0?wx_fmt=jpeg",
                                                "content_url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=1&sn=584bdd35d9053597a09b093ecf27fd35&chksm=7d6ee8864a196190f04d451fe7640d0c90fe17c06be6824980475c0b6fbb4e7f329b267e4452#rd",
                                                "source_url": "https://baidu.com"
                                            },
                                            {
                                                "title": "测试图文2标题",
                                                "author": "测试图文2作者",
                                                "digest": "测试图文2摘要",
                                                "show_cover": 0,
                                                "cover_url": "http://mmbiz.qpic.cn/mmbiz_jpg/wWibW2Saqk7fwakIgv3EuS6WA8W7duyjZDpdSVkibEFdJ5WApOQgL2c6m26eJpVOS4BEvFkBvl4CAfHzJAbYFQXw/0?wx_fmt=jpeg",
                                                "content_url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=2&sn=09ae15421414ed15270ae24b2fd1f7c2&chksm=7d6ee8864a1961900e4b1ee9122ab6ee5a6f9887d4d032e4afff440ecd19e6b894a5b45d86f6#rd",
                                                "source_url": ""
                                            },
                                            {
                                                "title": "无封面",
                                                "author": "",
                                                "digest": "大字小字",
                                                "show_cover": 0,
                                                "cover_url": "",
                                                "content_url": "http://mp.weixin.qq.com/s?__biz=MzU3ODgxNDE4OA==&mid=100000005&idx=3&sn=dbfdef0488b1a7edb7d096644b1519df&chksm=7d6ee8864a196190e84bf2e74eb62f9887f41dd1ccda4fa5d57a62e508ff5f57a02d1fd42154#rd",
                                                "source_url": ""
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

    @property
    def self_menu_data(self):
        return {
            "is_menu_open": 1,
            "selfmenu_info": {
                "button": [
                    {
                        "name": "测试菜单",
                        "sub_button": {
                            "list": [
                                {
                                    "type": "view",
                                    "name": "abc",
                                    "url": "http://baidu.com/"
                                },
                                {
                                    "type": "click",
                                    "name": "第二个",
                                    "key": "abc"
                                }
                            ]
                        }
                    },
                    {
                        "name": "测试2",
                        "sub_button": {
                            "list": [
                                {
                                    "type": "click",
                                    "name": "aaaa",
                                    "key": "6666"
                                }
                            ]
                        }
                    }
                ]
            }
        }
    #endregion
