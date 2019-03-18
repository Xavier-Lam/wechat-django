# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from wechatpy.client.api import WeChatGroup, WeChatTag

from ..models import UserTag, WeChatUser
from .base import mock, WeChatTestCase


class UserTestCase(WeChatTestCase):
    def test_sync(self):
        """测试同步用户标签"""
        def assertTagSyncSuccess(custom_tags):
            with mock.patch.object(WeChatGroup, "get"),\
                mock.patch.object(WeChatTag, "update"),\
                mock.patch.object(WeChatTag, "create"):
                remote_tags = self.base_tags[:] + [
                    dict(
                        id=id,
                        name=name,
                        count=0
                    )
                    for id, name in custom_tags.items()
                ]
                WeChatGroup.get.return_value = remote_tags
                # 不会调用远程接口
                WeChatTag.update.side_effect = Exception()
                WeChatTag.create.side_effect = Exception()

                UserTag.sync(self.app)
                tags = UserTag.objects.filter(app=self.app).all()
                self.assertEqual(len(tags), len(remote_tags))
                # 检查每个tag被正确插入
                for tag in remote_tags:
                    UserTag.objects.get(app=self.app, id=tag["id"], name=tag["name"])

        assertTagSyncSuccess({101: "group1", 102: "group2"})
        assertTagSyncSuccess({103: "group1", 102: "group2"})
        assertTagSyncSuccess({104: "group3"})

    def test_sync_users(self):
        """测试同步标签下的用户"""
        with mock.patch.object(WeChatTag, "iter_tag_users"),\
            mock.patch.object(WeChatUser, "upsert_users"):

            WeChatTag.iter_tag_users.return_value = ["openid1", "openid2"]
            WeChatUser.upsert_users.return_value = ["openid1", "openid2"]
            tag = UserTag.objects.create(app=self.app, name="tag", id=101)
            self.assertEqual(tag.sync_users(False), ["openid1", "openid2"])

    def test_change_user_tags(self):
        """测试用户标签变更"""
        tag_user_err = "tag_user_err"
        untag_user_err = "untag_user_err"

        user = WeChatUser.objects.create(app=self.app, openid="openid1")
        tag1 = UserTag.objects.create(app=self.app, id=101, name="tag1")
        tag2 = UserTag.objects.create(app=self.app, id=102, name="tag2")

        with mock.patch.object(WeChatTag, "tag_user"),\
            mock.patch.object(WeChatTag, "untag_user"):

            # 测试用户添加标签
            WeChatTag.untag_user.side_effect = Exception(untag_user_err)
            user.tags.set((tag1,))
            user.tags.filter(id=tag1.id).get()
            self.assertEqual(WeChatTag.tag_user.call_args, ((tag1.id, user.openid),))

            user.tags.set((tag1, tag2))
            self.assertEqual(user.tags.count(), 2)
            self.assertEqual(
                WeChatTag.tag_user.call_args, ((tag2.id, user.openid),))

            # 测试用户加减标签
            WeChatTag.untag_user.side_effect = None
            WeChatTag.tag_user.side_effect = Exception(tag_user_err)
            user.tags.set((tag2, ))
            self.assertEqual(user.tags.count(), 1)
            self.assertEqual(
                WeChatTag.untag_user.call_args, ((tag1.id, user.openid),))

            # 测试用户加减标签异常
            WeChatTag.untag_user.side_effect = Exception(untag_user_err)

            with transaction.atomic(), self.assertRaises(Exception) as context:
                user.tags.add(tag1)
            self.assertIn(tag_user_err, str(context.exception))
            self.assertRaises(
                UserTag.DoesNotExist,
                lambda: user.tags.get(app=self.app, id=tag1.id))

            with transaction.atomic(), self.assertRaises(Exception) as context:
                user.tags.remove(tag2)
            self.assertIn(untag_user_err, str(context.exception))
            user.tags.get(app=self.app, id=tag2.id)

    def test_tag_users(self):
        """测试标签用户变更"""
        tag_user_err = "tag_user_err"
        untag_user_err = "untag_user_err"

        user1 = WeChatUser.objects.create(app=self.app, openid="openid1")
        user2 = WeChatUser.objects.create(app=self.app, openid="openid2")
        tag = UserTag.objects.create(app=self.app, id=101, name="tag1")

        with mock.patch.object(WeChatTag, "tag_user"),\
            mock.patch.object(WeChatTag, "untag_user"):

            # 测试标签添加用户
            WeChatTag.untag_user.side_effect = Exception(untag_user_err)
            tag.users.set((user1,))
            tag.users.filter(openid=user1.openid).get()
            self.assertEqual(WeChatTag.tag_user.call_args, ((tag.id, [user1.openid]),))

            tag.users.set((user1, user2))
            self.assertEqual(tag.users.count(), 2)
            self.assertEqual(
                WeChatTag.tag_user.call_args, ((tag.id, [user2.openid]),))

            # 测试标签加减用户
            WeChatTag.untag_user.side_effect = None
            WeChatTag.tag_user.side_effect = Exception(tag_user_err)
            tag.users.set((user2, ))
            self.assertEqual(tag.users.count(), 1)
            self.assertEqual(
                WeChatTag.untag_user.call_args, ((tag.id, [user1.openid]),))

            # 测试标签加减用户异常
            WeChatTag.untag_user.side_effect = Exception(untag_user_err)

            with transaction.atomic(), self.assertRaises(Exception) as context:
                tag.users.add(user1)
            self.assertIn(tag_user_err, str(context.exception))
            self.assertRaises(
                WeChatUser.DoesNotExist,
                lambda: tag.users.get(app=self.app, openid=user1.openid))

            with transaction.atomic(), self.assertRaises(Exception) as context:
                tag.users.remove(user2)
            self.assertIn(untag_user_err, str(context.exception))
            tag.users.get(app=self.app, openid=user2.openid)

    def test_edit_tag(self):
        """测试标签的增删改"""
        id = 101
        name = "group1"
        # 新增
        with mock.patch.object(WeChatTag, "create"):
            WeChatTag.create.return_value = dict(
                id=id,
                name=name
            )
            UserTag(app=self.app, name=name).save()
            tag = UserTag.objects.get(app=self.app, name=name)
            self.assertEqual(tag.id, id)
            self.assertEqual(WeChatTag.create.call_args, ((name,),))

        name = "edit"
        with mock.patch.object(WeChatTag, "update"):
            tag.name = name
            tag.save()
            tag = UserTag.objects.get(app=self.app, name=name)
            self.assertEqual(tag.id, id)
            self.assertEqual(WeChatTag.update.call_args, ((id, name),))

        with mock.patch.object(WeChatTag, "delete"):
            tag.delete()
            self.assertRaises(
                UserTag.DoesNotExist,
                lambda: UserTag.objects.get(app=self.app, id=id))
            self.assertEqual(WeChatTag.delete.call_args, ((id,),))

    @property
    def base_tags(self):
        return [
            {
                "id": 0,
                "name": "未分组",
                "count": 0
            },
            {
                "id": 1,
                "name": "黑名单",
                "count": 0
            },
            {
                "id": 2,
                "name": "星标组",
                "count": 0
            }
        ]
