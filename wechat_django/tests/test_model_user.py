# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import django
from django.db import models as m
from django.db.backends.sqlite3 import schema
from django_fake_model.models import FakeModel
from wechatpy.exceptions import InvalidSignatureException

from ..models import (MiniProgramUser, PublicApp, PublicUser, Session,
                      WeChatUser)
from .base import mock, WeChatTestCase


class FakeUserForeignKeyModel(FakeModel):
    user = m.ForeignKey(WeChatUser, on_delete=m.CASCADE, null=False,
                        related_name="fakes")


class UserTestCase(WeChatTestCase):

    @classmethod
    def setUpClass(cls):
        super(UserTestCase, cls).setUpClass()
        if django.VERSION[0] >= 2:
            schema.DatabaseSchemaEditor.__enter__ = \
                schema.BaseDatabaseSchemaEditor.__enter__

    def test_sync(self):
        """测试同步用户"""
        pass

    def test_fetch_users(self):
        """测试拉取用户"""
        pass

    def test_upsert_users(self):
        """测试插入或更新用户"""
        # 插入openid
        openids = ["openid1", "openid2", "openid3"]
        users = self.app.users.bulk_upsert(openids)
        user_openids = [u.openid for u in users]
        self.assertEqual(openids, user_openids)
        for u in users:
            self.assertTrue(u.id)

        # 单个
        openid = "openid4"
        user, created = self.app.users.upsert(openid=openid)
        id = user.id
        self.assertTrue(id)
        self.assertEqual(user.openid, openid)
        self.assertTrue(created)
        nickname = "nickname"
        user, created = self.app.users.upsert(openid=openid,
                                              nickname=nickname)
        self.assertFalse(created)
        self.assertEqual(user.id, id)
        self.assertEqual(user.nickname, nickname)

        # 多个更新字典
        data = [
            dict(openid="openid1", nickname="nickname1"),
            dict(openid="openid2", nickname="nickname2"),
            dict(openid="openid3", nickname="nickname3"),
            dict(openid="openid5", nickname="nickname5")
        ]
        users = self.app.users.bulk_upsert(data)
        user_openids = [u.openid for u in users]
        user_nicknames = [u.nickname for u in users]
        self.assertEqual([o["openid"] for o in data], user_openids)
        self.assertEqual([o["nickname"] for o in data], user_nicknames)
        for u in users:
            self.assertTrue(u.id)

    def test_update(self):
        """测试更新用户"""
        # 测试公众号用户不传user_dict调用接口更新
        openid = "openid"
        user, created = self.app.users.upsert(openid=openid)
        with mock.patch.object(PublicApp, "fetch_user"):
            user.update()
            self.assertEqual(PublicApp.fetch_user.call_args[0][0], openid)

    def test_miniprogram_messages(self):
        """测试小程序消息解析"""
        self.miniprogram.appid = "wx4f4bc4dec97d474b"
        session_key = "HyVFkGl5F5OQWJZZaNzBBg=="
        user = MiniProgramUser.objects.create(openid="openid",
                                              app=self.miniprogram)
        Session.objects.create(
            user=user,
            auth=dict(session_key=session_key)
        )
        session = user.session

        # 验证签名
        raw_data = '{"nickName":"Band","gender":1,"language":"zh_CN","city":"Guangzhou","province":"Guangdong","country":"CN","avatarUrl":"http://wx.qlogo.cn/mmopen/vi_32/1vZvI39NWFQ9XM4LtQpFrQJ1xlgZxx3w7bQxKARol6503Iuswjjn6nIGBiaycAjAtpujxyzYsrztuuICqIM5ibXQ/0"}' # noqa
        sign = "75e81ceda165f4ffa64f4068af58c64b8f54b88c"
        data = session.validate_message(raw_data, sign)
        self.assertEqual(data, json.loads(raw_data))
        sign = "fake_sign"
        self.assertRaises(
            InvalidSignatureException, session.validate_message,
            raw_data, sign)

        # 解密
        session.auth["session_key"] = "tiihtNczf5v6AKRyjwEUhQ=="
        encrypted_data = "CiyLU1Aw2KjvrjMdj8YKliAjtP4gsMZMQmRzooG2xrDcvSnxIMXFufNstNGTyaGS9uT5geRa0W4oTOb1WT7fJlAC+oNPdbB+3hVbJSRgv+4lGOETKUQz6OYStslQ142dNCuabNPGBzlooOmB231qMM85d2/fV6ChevvXvQP8Hkue1poOFtnEtpyxVLW1zAo6/1Xx1COxFvrc2d7UL/lmHInNlxuacJXwu0fjpXfz/YqYzBIBzD6WUfTIF9GRHpOn/Hz7saL8xz+W//FRAUid1OksQaQx4CMs8LOddcQhULW4ucetDf96JcR3g0gfRK4PC7E/r7Z6xNrXd2UIeorGj5Ef7b1pJAYB6Y5anaHqZ9J6nKEBvB4DnNLIVWSgARns/8wR2SiRS7MNACwTyrGvt9ts8p12PKFdlqYTopNHR1Vf7XjfhQlVsAJdNiKdYmYVoKlaRv85IfVunYzO0IKXsyl7JCUjCpoG20f0a04COwfneQAGGwd5oa+T8yO5hzuyDb/XcxxmK01EpqOyuxINew==" # noqa
        iv = "r7BXXKkLb8qrSNn05n0qiA=="
        decrypted = session.decrypt_message(encrypted_data, iv)
        self.assertEqual(self.miniprogram.appid,
                         decrypted["watermark"]["appid"])
        fake_encrypted_data = "abc"
        self.assertRaises(
            (TypeError, ValueError), session.decrypt_message,
            fake_encrypted_data, iv)
        fake_iv = "abc"
        self.assertRaises(
            (TypeError, ValueError), session.decrypt_message, encrypted_data,
            fake_iv)
        exipred_session_key = "abc"
        session.auth["session_key"] = exipred_session_key
        self.assertRaises(
            (TypeError, ValueError), session.decrypt_message, encrypted_data,
            iv)

    def test_update_by_user_dict(self):
        """小程序用户数据更新"""
        openid = "openid"
        user = MiniProgramUser.objects.create(app=self.miniprogram,
                                              openid=openid)
        origin_dict = {
            "nickName": "Band",
            "gender": 1,
            "language": "zh_CN",
            "city": "Guangzhou",
            "province": "Guangdong",
            "country": "CN",
            "avatarUrl": "http://wx.qlogo.cn/mmopen/vi_32/1vZvI39NWFQ9XM4LtQpFrQJ1xlgZxx3w7bQxKARol6503Iuswjjn6nIGBiaycAjAtpujxyzYsrztuuICqIM5ibXQ/0"
        }
        user_dict = origin_dict.copy()
        user.update(user_dict)
        self.assertEqual(user.nickname, origin_dict["nickName"])
        self.assertEqual(user.sex, origin_dict["gender"])
        self.assertEqual(user.language, origin_dict["language"])
        self.assertEqual(user.city, origin_dict["city"])
        self.assertEqual(user.province, origin_dict["province"])
        self.assertEqual(user.country, origin_dict["country"])
        self.assertEqual(user.headimgurl, origin_dict["avatarUrl"])
        self.assertEqual(user.avatar, origin_dict["avatarUrl"])
        self.assertEqual(user.avatar(132), "http://wx.qlogo.cn/mmopen/vi_32/1vZvI39NWFQ9XM4LtQpFrQJ1xlgZxx3w7bQxKARol6503Iuswjjn6nIGBiaycAjAtpujxyzYsrztuuICqIM5ibXQ/132")

    def test_queryset(self):
        """测试关联queryset"""

        self.assertEqual(self.app.users.model, PublicUser)
        self.assertEqual(self.subscribe.users.model, PublicUser)
        self.assertEqual(self.miniprogram.users.model, MiniProgramUser)
        self.assertEqual(self.webapp.users.model, WeChatUser)

    @FakeUserForeignKeyModel.fake_me
    def test_user_model(self):
        """测试能拿到正确的user类型"""

        def assert_type_correct(app, user_type):
            # 由反向related获取
            user = app.users.create(openid="openid")
            self.assertTrue(isinstance(user, user_type))
            user = app.users.get(openid="openid")
            self.assertTrue(isinstance(user, user_type))

            # 由本类直接获取
            user = user_type.objects.create(app=app, openid="openid2")
            self.assertTrue(isinstance(user, user_type))
            user = user_type.objects.get(app=app, openid="openid2")
            self.assertTrue(isinstance(user, user_type))

            # 由基类获取
            user = WeChatUser.objects.create(app=app, openid="openid3")
            self.assertTrue(isinstance(user, user_type))
            user = WeChatUser.objects.get(app=app, openid="openid3")
            self.assertTrue(isinstance(user, user_type))

            # Foreignkey获取
            fake = FakeUserForeignKeyModel.objects.create(user=user)
            self.assertTrue(isinstance(fake.user, user_type))
            fake = FakeUserForeignKeyModel.objects.get(id=fake.id)
            self.assertTrue(isinstance(fake.user, user_type))

        # 服务号用户
        assert_type_correct(self.app, PublicUser)
        # 订阅号
        assert_type_correct(self.subscribe, PublicUser)
        # 小程序
        assert_type_correct(self.miniprogram, MiniProgramUser)
        # 其他
        assert_type_correct(self.webapp, WeChatUser)
