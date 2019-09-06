# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m, transaction
from django.utils.translation import ugettext_lazy as _

from ..utils.model import model_fields
from . import appmethod, Material, WeChatModel


class Article(WeChatModel):
    material = m.ForeignKey(
        Material, related_name="articles", on_delete=m.CASCADE)

    title = m.CharField(_("title"), max_length=64)
    thumb_media_id = m.CharField(_("thumb_media_id"), max_length=64)
    show_cover_pic = m.BooleanField(_("show cover"), default=True)
    author = m.CharField(
        _("author"), max_length=24, blank=True, null=True, default="")
    digest = m.CharField(
        _("digest"), max_length=256, blank=True, null=True, default="")
    content = m.TextField(_("content"))
    url = m.CharField(_("url"), max_length=256)
    content_source_url = m.CharField(
        _("content source url"), max_length=256)

    need_open_comment = m.NullBooleanField(
        _("need open comment"), default=None)
    only_fans_can_comment = m.NullBooleanField(
        _("only fans can comment"), default=None)

    index = m.PositiveSmallIntegerField(_("index"))
    _thumb_url = m.CharField(
        db_column="thumb_url", max_length=256, null=True, default=None)

    synced_at = m.DateTimeField(_("synchronized at"), auto_now_add=True)

    class Meta(object):
        verbose_name = _("article")
        verbose_name_plural = _("articles")

        unique_together = (("material", "index"),)
        ordering = ("material", "index")

    @property
    def app(self):
        return self.material and self.material.app

    @property
    def app_id(self):
        return self.material and self.material.app_id

    @property
    def thumb_url(self):
        if self._thumb_url is None and self.thumb_media_id:
            # 不存在url时通过thumb_media_id同步
            image = self.app.materials.filter(
                media_id=self.thumb_media_id).first()
            self._thumb_url = image and image.url
            self._thumb_url is not None and self.save()
        return self._thumb_url

    @thumb_url.setter
    def thumb_url(self, value):
        self._thumb_url = value

    @appmethod("sync_articles")
    def sync(cls, app, id=None):
        if id:
            return app.sync_materials(id, Material.Type.NEWS)
        else:
            with transaction.atomic():
                return app.sync_type_materials(Material.Type.NEWS)

    @appmethod("migrate_articles")
    def migrate(cls, app, src, media_id=None):
        """
        从src迁移图文到app
        """
        if media_id:
            news = src.download_material(media_id)
            return cls._migrate_news(app, src, news)
        else:
            data = src.get_materials(Material.Type.NEWS)
            return [cls._migrate_news(app, src, news) for news in data]

    @classmethod
    def _migrate_news(cls, app, src, news):
        articles = cls.from_mp(news)
        for article in articles:
            article.thumb_url = None
            # 重新传所有thumb_media_id
            if article.thumb_media_id:
                resp = src.download_material(article.thumb_media_id)
                if not resp.content:
                    # 实验发现存在返回空串的情况 应该是没有配置封面
                    raise ValueError("没有配置封面")
                else:
                    thumb_media = app.upload_material(
                        resp, Material.Type.IMAGE, permenant=True, save=True)
                    article.thumb_media_id = thumb_media.media_id

        # 创建图文
        return app.upload_material(
            [article.to_json() for article in articles],
            type=Material.Type.NEWS)

    @classmethod
    def from_mp(cls, data, news=None):
        articles = (data.get("content") or data)["news_item"]
        fields = model_fields(cls)
        return [
            cls(
                index=idx,
                material=news,
                _thumb_url=article.get("thumb_url"),
                **{k: v for k, v in article.items() if k in fields}
            )
            for idx, article in enumerate(articles)
        ]

    def to_json(self):
        return dict(
            title=self.title,
            thumb_media_id=self.thumb_media_id,
            show_cover_pic=1 if self.show_cover_pic else 0,
            need_open_comment=1 if self.need_open_comment else 0,
            only_fans_can_comment=1 if self.only_fans_can_comment else 0,
            author=self.author,
            digest=self.digest,
            content=self.content,
            url=self.url,
            content_source_url=self.content_source_url
        )

    def __str__(self):
        return "{0}".format(self.title)
