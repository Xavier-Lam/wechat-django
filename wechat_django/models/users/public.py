# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import transaction
from django.utils import timezone as tz
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from wechat_django.models import PublicApp
from wechat_django.utils.func import next_chunk
from wechat_django.utils.model import model_fields
from .base import WeChatUser


class PublicUser(WeChatUser):
    """公众号用户"""

    @property
    def group(self):
        from . import UserTag
        try:
            return self.app.user_tags.get(id=self.groupid).name
        except UserTag.DoesNotExist:
            return None

    # TODO: 移到根类
    @PublicApp.shortcut
    def user_by_openid(cls, app, openid, ignore_errors=False, sync_user=True):
        """根据用户openid拿到用户对象
        :param ignore_errors: 当库中未找到用户或接口返回失败时还是强行插入user
        :param sync_user: 从服务器拿用户数据
        """
        try:
            return app.users.get(openid=openid)
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
        fields = model_fields(cls)
        # TODO: 根据当前语言拉取用户数据
        user_dicts = app.client.user.get_batch(openids)
        update_dicts = map(
            lambda o: {k: v for k, v in o.items() if k in fields},
            user_dicts
        )
        rv = []
        with transaction.atomic():
            tags = list(app.user_tags.all())

            for user_dict in user_dicts:
                defaults = {k: v for k, v in user_dict.items() if k in fields}
                defaults["synced_at"] = tz.now()
                user = cls.objects.update_or_create(
                    defaults=defaults,
                    app=app,
                    openid=defaults["openid"]
                )[0]

                # 拉取标签数据
                tagid_list = user_dict.get("tagid_list")
                if tagid_list:
                    user._tag_local = True
                    user_tags = list(filter(lambda o: o.id in tagid_list, tags))

                    if len(user_tags) != len(tagid_list):
                        # 标签没有完全同步
                        tags = app.sync_usertags()
                        user_tags = list(filter(lambda o: o.id in tagid_list, tags))

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
