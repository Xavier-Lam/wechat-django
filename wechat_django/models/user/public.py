# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.utils import timezone as tz
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from wechat_django.models import PublicApp, ServiceApp, SubscribeApp
from wechat_django.utils.func import next_chunk
from .base import WeChatUser


@ServiceApp.register_model
@SubscribeApp.register_model
class PublicUser(WeChatUser):
    """公众号用户"""

    @property
    def group(self):
        try:
            return self.app.user_tags.get(id=self.groupid).name
        except self.tags.model.DoesNotExist:
            return None

    @PublicApp.shortcut
    def user_by_openid(cls, app, openid, ignore_errors=False, sync_user=True):
        """根据用户openid拿到用户对象
        :param ignore_errors: 当库中未找到用户或接口返回失败时还是强行插入user
        :param sync_user: 从服务器拿用户数据
        """
        try:
            return super(PublicUser, cls).user_by_openid(app, openid,
                                                         ignore_errors=False)
        except WeChatUser.DoesNotExist:
            if sync_user:
                try:
                    return app.fetch_user(openid)
                except Exception as e:
                    if isinstance(e, WeChatClientException)\
                       and e.errcode == WeChatErrorCode.INVALID_OPENID:
                        # 不存在抛异常
                        raise
                    elif ignore_errors:
                        pass  # TODO: 好歹记个日志吧...
                    else:
                        raise
            elif not ignore_errors:
                raise
        return app.users.create(openid=openid)

    @PublicApp.shortcut("sync_users")
    def sync(cls, app, all=False, detail=True):
        """
        :type app: wechat_django.models.WeChatApp
        :param all: 是否重新同步所有用户
        :param detail: 是否同步用户详情
        """
        # 只有重新同步详情的才能全量同步
        all = all and detail

        users = []
        next_openid = not all and app.ext_info.get("last_openid") or None

        iterator = app.client.user.iter_followers(next_openid)
        for openids in next_chunk(iterator):
            if detail:
                users_chunk = app.fetch_users(openids)
            else:
                users_chunk = app.users.bulk_upsert(openids)
            users.extend(users_chunk)
            # 更新最后更新openid
            app.ext_info["last_openid"] = openids[-1]
            app.save()
        return users

    @PublicApp.shortcut
    def fetch_user(cls, app, openid):
        # NotFound重新抛出40003异常
        return app.fetch_users([openid]).pop()

    @PublicApp.shortcut
    def fetch_users(cls, app, openids):
        # TODO: 根据当前语言拉取用户数据
        user_dicts = app.client.user.get_batch(openids)
        rv = []
        with transaction.atomic():
            tags = list(app.user_tags.all())

            for user_dict in user_dicts:
                user_dict["synced_at"] = tz.now()
                user = app.users.upsert(**user_dict)[0]

                # 拉取标签数据
                tagids = user_dict.get("tagid_list")
                if tagids:
                    user._tag_local = True
                    user_tags = list(filter(lambda o: o.id in tagids, tags))

                    if len(user_tags) != len(tagids):
                        # 标签没有完全同步
                        tags = app.sync_usertags()
                        user_tags = list(filter(lambda o: o.id in tagids, tags))

                    user.tags.set(user_tags, clear=False)
                    user.save()

                    user._tag_local = False

                rv.append(user)

            return rv

    def update(self, user_dict=None):
        if user_dict:
            super(PublicUser, self).update(user_dict)
        else:
            self.app.fetch_user(self.openid)
            self.refresh_from_db()

    class Meta(object):
        proxy = True
