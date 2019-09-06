# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m, transaction
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..utils.func import next_chunk
from . import appmethod, WeChatApp, WeChatModel, WeChatUser


class UserTag(WeChatModel):
    SYS_TAGS = (0, 1, 2)

    _id = m.AutoField(primary_key=True)

    app = m.ForeignKey(
        WeChatApp, related_name="user_tags", null=False, editable=False,
        on_delete=m.CASCADE)
    id = m.IntegerField(_("tag id"))
    name = m.CharField(_("tag name"), max_length=30)
    users = m.ManyToManyField(WeChatUser, related_name="tags")

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)

    class Meta(object):
        verbose_name = _("user tag")
        verbose_name_plural = _("user tags")

        unique_together = (("app", "id"), )
        index_together = (("app", "name"), )
        ordering = ("app", "id")

    @property
    def sys_tag(self):
        return self.id in self.SYS_TAGS

    def __init__(self, *args, **kwargs):
        tag_local = kwargs.pop("_tag_local", None)
        super(UserTag, self).__init__(*args, **kwargs)
        self._tag_local = tag_local

    @appmethod("sync_usertags")
    def sync(cls, app):
        rv = []
        with transaction.atomic():
            db_tags = app.user_tags.all()
            db_tag_ids = {tag.id for tag in db_tags}
            tags = app.client.group.get()

            # 处理已经移除的tags
            deleted_tag_ids = db_tag_ids.difference(
                {tag["id"] for tag in tags})
            app.user_tags.filter(id__in=deleted_tag_ids).delete()

            for tag in tags:
                data = dict(id=tag["id"], name=tag["name"])
                if tag["id"] not in db_tag_ids:
                    db_tag = app.user_tags.create(_tag_local=True, **data)
                else:
                    db_tag = (app.user_tags.filter(id=tag["id"])
                        .update(name=tag["name"]))
                rv.append(db_tag)
            # 存在一个问题
            # 如果先同步了用户 id 101的tag名为a 假设u用户被打了tag a
            # 随后在其他平台移除了tag a 新建了tag b tag b的id恰好为101
            # 重新同步标签 u用户外键依然保留 而tag a已经被删除了
            # 这时这名用户会被认为是tag b的用户
            return rv

    def sync_users(self, detail=True):
        """同步该标签下的所有用户
        :param detail: 是否同步用户详情
        """
        rv = []
        iterator = self.app.client.tag.iter_tag_users(self.id)
        for openids in next_chunk(iterator):
            users = WeChatUser.upsert_users(self.app, openids, detail)
            rv.extend(users)
        return users

    def save(self, *args, **kwargs):
        # 保存之前 先创建标签
        if not getattr(self, "_tag_local", False):
            if self.sys_tag:
                raise ValueError(_("can not edit a system tag"))

            if self.id:
                # TODO: 未修改标签不要更新
                self.app.client.tag.update(self.id, self.name)
            else:
                data = self.app.client.tag.create(self.name)
                self.id = data["id"]
        return super(UserTag, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        take = 50
        limit = 100000
        count = self.users.count()
        if count > limit:
            # 当count 当于100,000时 要先untag users
            diff = count - limit
            for i in range(0, diff, take):
                # 每次只能至多untag 50条记录
                users = self.users.all()[:50]
                self.users.remove(users)

        self.app.client.tag.delete(self.id)
        return super(UserTag, self).delete(*args, **kwargs)

    def __str__(self):
        return self.name


@receiver(m.signals.m2m_changed, sender=UserTag.users.through)
def tag_user_changed(sender, instance, action, *args, **kwargs):
    """给某个标签添加多个用户"""
    if not kwargs["reverse"] and not getattr(instance, "_tag_local", False):
        users = WeChatUser.objects.filter(id__in=kwargs["pk_set"]).all()
        openids = [user.openid for user in users]
        client = instance.app.client.tag
        if action == "pre_add":
            client.tag_user(instance.id, openids)
        elif action == "pre_remove":
            client.untag_user(instance.id, openids)


@receiver(m.signals.m2m_changed, sender=WeChatUser.tags.through)
def user_tag_changed(sender, instance, action, *args, **kwargs):
    """给某个用户添加多个标签"""
    if kwargs["reverse"] and not getattr(instance, "_tag_local", False):
        tags = UserTag.objects.filter(_id__in=kwargs["pk_set"]).all()
        tag_ids = [tag.id for tag in tags]
        client = instance.app.client.tag
        for tag in tags:
            if action == "pre_add":
                client.tag_user(tag.id, instance.openid)
            elif action == "pre_remove":
                client.untag_user(tag.id, instance.openid)
