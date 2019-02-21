# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m, transaction
from django.utils.translation import ugettext_lazy as _

from . import Material


class Article(m.Model):
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
            image = Material.objects.filter(
                app=self.app, media_id=self.thumb_media_id).first()
            self._thumb_url = image and image.url
            self._thumb_url is not None and self.save()
        return self._thumb_url

    @thumb_url.setter
    def thumb_url(self, value):
        self._thumb_url = value

    @classmethod
    def sync(cls, app, id=None):
        if id:
            return Material.sync(app, id, Material.Type.NEWS)
        else:
            with transaction.atomic():
                return Material.sync_type(Material.Type.NEWS, app)

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
