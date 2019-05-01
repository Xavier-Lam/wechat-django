# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from wechatpy.exceptions import InvalidSignatureException

from ..models import Session, WeChatUser
from .base import mock, WeChatTestCase


class UserTestCase(WeChatTestCase):
    def test_sync(self):
        """测试同步用户"""
        pass

    def test_fetch_users(self):
        """测试拉取用户"""
        pass

    def test_upsert_users(self):
        """测试插入或更新用户"""
        pass

    def test_update(self):
        """测试更新用户"""
        pass

    def test_miniprogram_messages(self):
        """测试小程序消息解析"""
        self.app.appid = "wx4f4bc4dec97d474b"
        session_key = "HyVFkGl5F5OQWJZZaNzBBg=="
        user = WeChatUser.objects.create(openid="openid", app=self.app)
        session = Session(
            user=user,
            type=Session.Type.MINIPROGRAM,
            auth=dict(session_key=session_key)
        )

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
        self.assertEqual(self.app.appid, decrypted["watermark"]["appid"])
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
        user = WeChatUser.objects.create(app=self.app, openid=openid)
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
