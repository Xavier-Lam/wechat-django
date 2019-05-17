# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.contrib.auth.models import User
from django.urls import reverse
from django.test import Client
from wechatpy.client import api

from .. import models
from .base import mock, WeChatTestCase


class AdminViewTestCase(WeChatTestCase):
    """测试各admin页面能正常访问"""
    def setUp(self):
        super(AdminViewTestCase, self).setUp()
        user = User.objects.create(
            username="admin", is_superuser=True, is_staff=True)
        user.set_password("123456")
        user.save()
        self.client.login(username="admin", password="123456")

    def test_indexes(self):
        """测试首页"""
        self.assertRequestSuccess(reverse("admin:index"))
        self.assertRequestSuccess(reverse("admin:app_list", kwargs=dict(
            app_label="wechat_django"
        )))
        self.assertRequestSuccess(reverse("admin:wechat_funcs_list", kwargs=dict(
            app_label="wechat_django",
            wechat_app_id=self.app.id
        )))

    def test_article_view(self):
        """测试图文"""
        self.assertModelViewSuccess(
            models.Article, excludes=("history", "delete", "change"),
            status={"add": 403})

        material = models.Material.objects.create(
            app=self.app,
            media_id="media_id"
        )
        article = models.Article.objects.create(
            material=material,
            content="",
            url="url",
            index=0
        )
        self.assertModelViewSuccess(
            models.Article, article.id, status={"add": 403, "delete": 403})

    def test_material_view(self):
        """测试素材"""
        self.assertModelViewSuccess(
            models.Material, excludes=("history", "delete", "change"),
            status={"add": 403})

        material = models.Material.objects.create(
            app=self.app,
            media_id="media_image",
            type=models.Material.Type.IMAGE
        )
        self.assertModelViewSuccess(
            models.Material, material.id, status={"add": 403})

        material = models.Material.objects.create(
            app=self.app,
            media_id="media_video",
            type=models.Material.Type.VIDEO
        )
        self.assertModelViewSuccess(
            models.Material, material.id, status={"add": 403})

        material = models.Material.objects.create(
            app=self.app,
            media_id="media_voice",
            type=models.Material.Type.VOICE
        )
        self.assertModelViewSuccess(
            models.Material, material.id, status={"add": 403})
        
        material = models.Material.objects.create(
            app=self.app,
            media_id="media_new"
        )
        article = models.Article.objects.create(
            material=material,
            content="",
            url="url",
            index=0
        )
        self.assertModelViewSuccess(
            models.Material, material.id, status={"add": 403})

    def test_menu_view(self):
        """测试菜单"""
        self.assertModelViewSuccess(
            models.Menu, excludes=("history", "delete", "change"))
        with mock.patch.object(api.WeChatMenu, "get_menu_info"):
            api.WeChatMenu.get_menu_info.return_value = self.load_data("self_menu_data")
            menus = models.Menu.sync(self.app)
        self.assertModelViewSuccess(models.Menu, menus[0].id)

    def test_messagehandler_view(self):
        """测试消息处理程序"""
        self.assertModelViewSuccess(
            models.MessageHandler, excludes=("history", "delete", "change"))

        handler = models.MessageHandler.objects.create_handler(
            rules=[
                models.Rule(type=models.Rule.Type.ALL)
            ],
            replies=[
                models.Reply(type=models.Reply.MsgType.TEXT, pattern="test")
            ],
            app=self.app
        )
        self.assertModelViewSuccess(models.MessageHandler, handler.id)

    def test_messagelog_view(self):
        """测试消息日志"""
        self.assertModelViewSuccess(
            models.MessageLog, excludes=("history", "delete", "change"),
            status={"add": 403})

        user = models.WeChatUser.objects.create(app=self.app, openid="openid")
        log = models.MessageLog.objects.create(
            app=self.app, user=user, type=models.Rule.ReceiveMsgType.TEXT,
            content={})
        self.assertModelViewSuccess(
            models.MessageLog, log.id, status={"add": 403})
    
    def test_user_view(self):
        """测试用户"""
        self.assertModelViewSuccess(
            models.WeChatUser, excludes=("history", "delete", "change"),
            status={"add": 403})

        user = models.WeChatUser.objects.create(app=self.app, openid="openid")
        self.assertModelViewSuccess(
            models.WeChatUser, user.id, status={"add": 403, "delete": 403})


    def test_usertag(self):
        """测试用户标签"""
        self.assertModelViewSuccess(
            models.UserTag, excludes=("history", "delete", "change"))

        tag = models.UserTag.objects.create(
            app=self.app, id=101, name="tag", _tag_local=True)
        self.assertModelViewSuccess(models.UserTag, tag.id)

    def test_template(self):
        """测试模板消息后台"""
        self.assertModelViewSuccess(
            models.Template, excludes=("history", "delete", "change"),
            status={"add": 403})

        template = models.Template.objects.create(
            app=self.app, template_id="t", title="title")
        self.assertModelViewSuccess(
            models.Template, template.id, status={"add": 403, "delete": 403})

    def test_app(self):
        """测试公众号"""
        self.assertModelViewSuccess(models.WeChatApp, self.app.id, wechat=False)

    def assertModelViewSuccess(self, model, id=None, excludes=None, status=None, wechat=True):
        excludes = excludes or tuple()
        status = status or {}
        model_name = model._meta.model_name

        def make_url(view, **kwargs):
            wechat and kwargs.update(wechat_app_id=self.app.id)
            pattern = "admin:%s_%s_%s" % ("wechat_django", model_name, view)
            return reverse(pattern, kwargs=kwargs)

        "changelist" not in excludes\
            and self.assertRequestSuccess(
                make_url("changelist"), status_code=status.get("changelist"))
        "add" not in excludes\
            and self.assertRequestSuccess(
                make_url("add"), status_code=status.get("add"))
        # self.assertRequestSuccess(make_url("autocomplete"))
        "history" not in excludes\
            and self.assertRequestSuccess(
                make_url("history", object_id=id),
                status_code=status.get("history"))
        "delete" not in excludes\
            and self.assertRequestSuccess(
                make_url("delete", object_id=id),
                status_code=status.get("delete"))
        "change" not in excludes\
            and self.assertRequestSuccess(
                make_url("change", object_id=id),
                status_code=status.get("change"))

    def assertRequestSuccess(self, url, method="get", **kwargs):
        status_code = kwargs.pop("status_code", None) or 200
        resp = getattr(self.client, method)(url, follow=True, **kwargs)
        self.assertSuccess(resp, status_code)
    
    def assertSuccess(self, resp, status=200):
        self.assertEqual(resp.status_code, status)
