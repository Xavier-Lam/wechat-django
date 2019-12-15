# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.db import models as m, transaction
from django.utils.translation import ugettext_lazy as _

from wechat_django.models import WeChatApp
from wechat_django.models.base import (WeChatFixTypeQuerySet,
                                       WeChatFixTypeManager, WeChatModel)
from wechat_django.utils.model import enum2choices, model_fields


class ProxyField(property):
    def __init__(self, fget, fset=None, fdel=None, doc=None):
        if not callable(fget):
            field_name = fget
            fget = lambda self: getattr(self, field_name)
            fset = lambda self, value: setattr(self, field_name, value)
        super(ProxyField, self).__init__(fget, fset, fdel, doc)


class WeChatUserQuerySet(WeChatFixTypeQuerySet):
    def upsert(self, openid, **kwargs):
        updates = {
            k: v for k, v in kwargs.items()
            if k in model_fields(self.model)
        }
        return self.update_or_create(app=self.app, openid=openid,
                                     defaults=updates)

    def bulk_upsert(self, dicts):
        def upsert(o):
            if isinstance(o, dict):
                return self.upsert(**o)
            else:
                return self.upsert(o)

        with transaction.atomic():
            return [o[0] for o in map(upsert, dicts)]


WeChatUserManager = WeChatFixTypeManager.from_queryset(WeChatUserQuerySet)


@WeChatApp.register
class WeChatUser(WeChatModel):
    class Gender(object):
        UNKNOWN = 0
        MALE = 1
        FEMALE = 2

    class SubscribeScene(object):
        ADD_SCENE_SEARCH = "ADD_SCENE_SEARCH"  # 公众号搜索
        ADD_SCENE_ACCOUNT_MIGRATION = "ADD_SCENE_ACCOUNT_MIGRATION"  # 公众号迁移
        ADD_SCENE_PROFILE_CARD = "ADD_SCENE_PROFILE_CARD"  # 名片分享
        ADD_SCENE_QR_CODE = "ADD_SCENE_QR_CODE"  # 扫描二维码
        ADD_SCENE_PROFILE_LINK = "ADD_SCENEPROFILE LINK"  # 图文页内名称点击
        ADD_SCENE_PROFILE_ITEM = "ADD_SCENE_PROFILE_ITEM"  # 图文页右上角菜单
        ADD_SCENE_PAID = "ADD_SCENE_PAID"  # 支付后关注
        ADD_SCENE_OTHERS = "ADD_SCENE_OTHERS"  # 其他

    app = m.ForeignKey(WeChatApp, related_name="users", on_delete=m.CASCADE,
                       null=False, editable=False)
    openid = m.CharField(_("openid"), max_length=36, null=False)
    unionid = m.CharField(_("unionid"), max_length=36, null=True)

    alias = m.CharField(_("alias"), max_length=16, blank=True, null=True,
                        help_text=_("用户别名,用于程序快速查询用户,"
                                    "单app下唯一"))

    nickname = m.CharField(_("nickname"), max_length=32, null=True)
    sex = m.SmallIntegerField(_("gender"), null=True,
                              choices=enum2choices(Gender))
    headimgurl = m.CharField(_("avatar"), max_length=256, null=True)
    city = m.CharField(_("city"), max_length=24, null=True)
    province = m.CharField(_("province"), max_length=24, null=True)
    country = m.CharField(_("country"), max_length=24, null=True)
    language = m.CharField(_("language"), max_length=24, null=True)

    subscribe = m.NullBooleanField(_("is subscribed"), null=True)
    subscribe_time = m.IntegerField(_("subscribe time"), null=True)
    subscribe_scene = m.CharField(_("subscribe scene"), max_length=32,
                                  null=True,
                                  choices=enum2choices(SubscribeScene))
    qr_scene = m.IntegerField(_("qr scene"), null=True)
    qr_scene_str = m.CharField(_("qr_scene_str"), max_length=64, null=True)

    remark = m.CharField(_("WeChat remark"), max_length=30, blank=True,
                         null=True)
    comment = m.TextField(_("remark"), blank=True, null=True)
    groupid = m.IntegerField(_("group id"), null=True)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    synced_at = m.DateTimeField(_("synchronized at"), null=True, default=None)

    objects = WeChatUserManager()

    is_staff = False
    is_active = True
    is_anonymous = False
    is_authenticated = True

    @property
    def avatar(self):
        """头像

        可通过user.avatar获取,或指定尺寸user.avatar(132)
        """
        def call(self, size=132):
            assert size in (0, 46, 64, 96, 132)
            return self and re.sub(r"\d+$", str(size), self)

        cls = type(str.__name__, (str,), dict(__call__=call))
        return cls(self.headimgurl)

    @avatar.setter
    def avatar(self, value):
        self.headimgurl = value

    gender = ProxyField("sex")

    @WeChatApp.shortcut
    def user_by_openid(cls, app, openid, ignore_errors=False):
        """根据用户openid拿到用户对象
        :param ignore_errors: 当库中未找到用户或接口返回失败时还是强行插入user
        """
        try:
            return app.users.get(openid=openid)
        except WeChatUser.DoesNotExist:
            if not ignore_errors:
                raise
        return app.users.create(openid=openid)

    def update(self, user_dict=None):
        """重新同步用户数据"""
        if user_dict:
            cls = self.__class__
            proxy_fields = [k for k in dir(cls)
                            if isinstance(getattr(cls, k), ProxyField)]
            field_names = model_fields(self)
            field_names = field_names.union(proxy_fields)
            for key in user_dict:
                if key.lower() in field_names:
                    setattr(self, key.lower(), user_dict[key])
            self.save()
            self.refresh_from_db()

    def save(self, *args, **kwargs):
        self.alias = self.alias or None
        return super(WeChatUser, self).save(*args, **kwargs)

    def __str__(self):
        return "{nickname}({openid})".format(nickname=self.nickname or "",
                                             openid=self.openid)

    class Meta(object):
        base_manager_name = "objects"
        verbose_name = _("user")
        verbose_name_plural = _("users")

        ordering = ("app", "-created_at")
        unique_together = (("app", "openid"), ("unionid", "app"),
                           ("app", "alias"))
