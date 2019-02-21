# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import mimetypes
import re

from django.db import models as m, transaction
from django.utils.translation import ugettext_lazy as _
from wechatpy.constants import WeChatErrorCode
from wechatpy.exceptions import WeChatClientException

from ..utils.admin import enum2choices
from . import WeChatApp


class MaterialManager(m.Manager):
    def get_by_media(self, app, media_id):
        return self.get(app=app, media_id=media_id)

    def create_material(self, app, type=None, **kwargs):
        """创建永久素材"""
        if type is None:
            raise NotImplementedError()
        if type == Material.Type.NEWS:
            return self.create_news(app, **kwargs)
        else:
            media_id = kwargs["media_id"]
            allowed_keys = set(map(lambda o: o.name, self.model._meta.fields))
            if type == Material.Type.VIDEO and "url" not in kwargs:
                data = app.client.material.get(media_id)
                kwargs["url"] = data.get("down_url")

            kwargs = {
                key: kwargs[key]
                for key in allowed_keys
                if key in kwargs
            }
            query = dict(app=app, type=type, media_id=media_id)
            record = dict(app=app, type=type, **kwargs)
            return self.update_or_create(defaults=record, **query)[0]

    def create_news(self, app, **kwargs):
        """创建永久图文素材"""
        from . import Article
        # 插入media
        query = dict(app=app, media_id=kwargs["media_id"])
        record = dict(
            type=Material.Type.NEWS,
            update_time=kwargs["update_time"]
        )
        record.update(query)
        news, created = self.update_or_create(record, **query)
        if not created:
            # 移除所有article重新插入
            news.articles.all().delete()

        articles = (kwargs.get("content") or kwargs)["news_item"]
        fields = set(map(lambda o: o.name, Article._meta.fields))
        Article.objects.bulk_create([
            Article(
                index=idx,
                material=news,
                _thumb_url=article.get("thumb_url"),
                **{k: v for k, v in article.items() if k in fields}  # 过滤article fields
            )
            for idx, article in enumerate(articles)
        ])
        return news


class Material(m.Model):
    class Type(object):
        IMAGE = "image"
        VIDEO = "video"
        NEWS = "news"
        VOICE = "voice"

    app = m.ForeignKey(
        WeChatApp, related_name="materials", on_delete=m.CASCADE)
    type = m.CharField(
        _("type"), max_length=5, choices=(enum2choices(Type)))
    media_id = m.CharField(_("media_id"), max_length=64)
    name = m.CharField(_("name"), max_length=64, blank=True, null=True)
    url = m.CharField(_("url"), max_length=512, editable=False, null=True)
    update_time = m.IntegerField(
        _("update time"), editable=False, null=True)

    comment = m.TextField(_("comment"), blank=True)

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    objects = MaterialManager()

    class Meta(object):
        verbose_name = _("material")
        verbose_name_plural = _("materials")

        unique_together = (("app", "media_id"),)
        ordering = ("app", "-update_time")

    @classmethod
    def sync(cls, app, id=None, type=None):
        """同步所有永久素材"""
        if id:
            if type not in (cls.Type.NEWS, cls.Type.VIDEO):
                raise NotImplementedError()
            data = app.client.material.get_raw(id)
            return cls.objects.create_material(
                app=app, type=type, media_id=id, **data)
        else:
            updated = []
            for type, _ in enum2choices(cls.Type):
                with transaction.atomic():
                    updates = cls.sync_type(type, app)
                    updated.extend(updates)
            return updated

    @classmethod
    def sync_type(cls, type, app):
        """同步某种类型的永久素材"""
        count = 20
        offset = 0
        updates = []
        while True:
            data = app.client.material.batchget(
                media_type=type,
                offset=offset,
                count=count
            )
            updates.extend(data["item"])
            if data["total_count"] <= offset + count:
                break
            offset += count
        # 删除被删除的 更新或新增获取的
        (cls.objects.filter(app=app, type=type)
            .exclude(media_id__in=map(lambda o: o["media_id"], updates))
            .delete())
        return [
            cls.objects.create_material(app=app, type=type, **item)
            for item in updates]

    @classmethod
    def as_permenant(cls, media_id, app, save=True):
        """将临时素材转换为永久素材"""
        # 下载临时素材
        resp = app.client.media.download(media_id)

        try:
            content_type = resp.headers["Content-Type"]
        except:
            raise ValueError("missing Content-Type")
        if content_type.startswith("image"):
            type = cls.Type.IMAGE
        elif content_type.startswith("video"):
            type = cls.Type.VIDEO
        elif content_type.startswith("audio"):
            type = cls.Type.VOICE
        else:
            raise ValueError("unknown Content-Type")

        # 找文件名
        try:
            disposition = resp.headers["Content-Disposition"]
            filename = re.findall(r'filename="(.+?)"', disposition)[0]
        except:
            # 默认文件名
            ext = mimetypes.guess_extension(content_type)
            filename = (media_id + ext) if ext else media_id

        # 上载素材
        return cls.upload_permenant(app, (filename, resp.content), type, save)

    @classmethod
    def upload_permenant(cls, app, file, type, save=True):
        """上传永久素材"""
        data = app.client.material.add(type, file)
        media_id = data["media_id"]
        if save:
            return cls.objects.create_material(
                app=app, type=type, media_id=media_id, url=data.get("url"))
        else:
            return media_id

    @classmethod
    def upload_temporary(cls, app, file, type):
        """上传临时素材
        :param type: image|voice|video|thumb
        """
        return app.client.media.upload(type, file)

    @property
    def articles_json(self):
        return list(map(lambda o: dict(
            title=o.title,
            description=o.digest,
            image=o.thumb_url,
            url=o.url
        ), self.articles))

    def delete(self, *args, **kwargs):
        # 先远程素材删除
        try:
            self.app.client.material.delete(self.media_id)
        except WeChatClientException as e:
            if e.errcode != WeChatErrorCode.INVALID_MEDIA_ID:
                raise
        rv = super(Material, self).delete(*args, **kwargs)
        return rv

    def __str__(self):
        media = "{type}:{media_id}".format(type=self.type, media_id=self.media_id)
        return "{0} ({1})".format(self.comment, media) if self.comment else media
