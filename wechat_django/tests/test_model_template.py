# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechatpy.client.api import WeChatMessage, WeChatTemplate, WeChatWxa

from ..models import Template, WeChatUser
from .base import mock, WeChatTestCase


class TemplateTestCase(WeChatTestCase):
    def test_sync_miniprogram(self):
        """测试同步小程序模板"""
        with mock.patch.object(WeChatWxa, "list_templates"):
            templates = [{
                "template_id": "wDYzYZVxobJivW9oMpSCpuvACOfJXQIoKUm0PY397Tc",
                "title": "购买成功通知",
                "content": "购买地点{{keyword1.DATA}}\n购买时间{{keyword2.DATA}}\n物品名称{{keyword3.DATA}}\n",
                "example": "购买地点：TIT造舰厂\n购买时间：2016年6月6日\n物品名称：咖啡\n"
            }]
            WeChatWxa.list_templates.return_value = templates

            # 同步
            self.miniprogram.sync_templates()
            self.assertTemplateEqual(self.miniprogram, templates)

            # 再次同步 结果一致
            self.miniprogram.sync_templates()
            self.assertTemplateEqual(self.miniprogram, templates)

    def test_sync_service(self):
        """测试同步服务号模板"""
        with mock.patch.object(WeChatTemplate, "get_all_private_template"):
            data = self.load_data("get_all_private_template")
            templates = data["template_list"]
            WeChatTemplate.get_all_private_template.return_value = data

            # 同步
            self.app.sync_templates()
            self.assertTemplateEqual(self.app, templates)

            # 再次同步 结果一致
            self.app.sync_templates()
            self.assertTemplateEqual(self.app, templates)

    def test_send_miniprogram(self):
        """测试发送小程序模板消息"""
        with mock.patch.object(WeChatWxa, "send_template_message"):
            id = "id"
            openid = "openid"
            form_id = "form_id"
            pagepath = "pagepath"
            emphasis_keyword = "keyword1.DATA"
            data = {
                "keyword1": {
                    "value": "339208499"
                },
                "keyword2": {
                    "value": "2015年01月05日 12:30"
                },
                "keyword3": {
                    "value": "粤海喜来登酒店"
                } ,
                "keyword4": {
                    "value": "广州市天河区天河路208号"
                }
            }

            t = Template(app=self.miniprogram, template_id=id)

            # 直接发送openid及data
            t.send(openid, data, form_id=form_id)
            self.assertCallArgsEqual(
                WeChatWxa.send_template_message, (openid, id, data, form_id))

            # 发送user及data
            user = WeChatUser(openid=openid)
            t.send(user, data, form_id=form_id)
            self.assertCallArgsEqual(
                WeChatWxa.send_template_message, (openid, id, data, form_id))

            # 发送data及page
            t.send(
                openid, data, form_id=form_id, pagepath=pagepath,
                emphasis_keyword=emphasis_keyword)
            self.assertCallArgsEqual(
                WeChatWxa.send_template_message, (openid, id, data, form_id),
                {"page": pagepath, "emphasis_keyword": emphasis_keyword})

            # 发送kwargs
            t.send(
                openid, form_id=form_id,
                **{k: v["value"] for k, v in data.items()})
            self.assertCallArgsEqual(
                WeChatWxa.send_template_message, (openid, id, data, form_id))

    def test_send_service(self):
        """测试发送服务号模板消息"""
        with mock.patch.object(WeChatMessage, "send_template"):
            id = "id"
            openid = "openid"
            url = "url"
            data = {
                "first": {
                    "value":"恭喜你购买成功！",
                    "color":"#173177"
                },
                "keyword1":{
                    "value":"巧克力",
                    "color":"#173177"
                },
                "keyword2": {
                    "value":"39.8元",
                    "color":"#173177"
                },
                "keyword3": {
                    "value":"2014年9月22日",
                    "color":"#173177"
                },
                "remark":{
                    "value":"欢迎再次购买！",
                    "color":"#173177"
                }
           }

            t = Template(app=self.app, template_id=id)

            # 发送data及url
            t.send(openid, data, url)
            self.assertCallArgsEqual(
                WeChatMessage.send_template, (openid, id, data), {"url": url})

            # 使用user对象
            user = WeChatUser(openid=openid)
            t.send(user, data)
            self.assertCallArgsEqual(
                WeChatMessage.send_template, (openid, id, data))

            # 发送data及小程序
            appid = "appid"
            pagepath = "pagepath"
            miniprogram = dict(
                appid=appid,
                pagepath=pagepath
            )
            t.send(openid, data, **miniprogram)
            self.assertCallArgsEqual(
                WeChatMessage.send_template, (openid, id, data),
                {"miniprogram": miniprogram})

            # 发送kwargs
            t.send(openid, **data)
            self.assertCallArgsEqual(
                WeChatMessage.send_template, (openid, id, data))

            # 发送str kwargs
            t.send(openid, **{k: v["value"] for k, v in data.items()})
            self.assertCallArgsEqual(
                WeChatMessage.send_template,
                (openid, id, {k: {"value": v["value"]} for k, v in data.items()}))

    def assertTemplateEqual(self, app, templates):
        """模板和同步的一致"""
        self.assertEqual(app.templates.count(), len(templates))
        for item in templates:
            template = app.templates.get(
                template_id=item["template_id"])
            for key, value in item.items():
                self.assertEqual(getattr(template, key), value)
