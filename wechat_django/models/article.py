from django.db import models as m
from django.utils.translation import ugettext as _

from . import Material, WeChatApp

class Article(m.Model):
    material = m.ForeignKey(Material, on_delete=m.CASCADE,
        related_name="articles")

    title = m.CharField(_("title"), max_length=64)
    thumb_media_id = m.CharField(_("thumb_media_id"), max_length=64)
    show_cover_pic = m.BooleanField(_("show cover"), default=True)
    author = m.CharField(_("author"), max_length=24,
        blank=True, null=True, default="")
    digest = m.CharField(_("digest"), max_length=256, 
        blank=True, null=True, default="")
    content = m.TextField(_("content"))
    url = m.CharField(_("url"), max_length=256)
    content_source_url = m.CharField(_("content source url"), max_length=256)

    index = m.PositiveSmallIntegerField(_("index"))
    img_url = m.CharField(max_length=256)

    synced_at = m.DateTimeField(_("updated"), auto_now_add=True)

    class Meta(object):
        unique_together = ("material", "index")
        ordering = ("material", "index")

    def to_json(self):
        return dict(
            title=self.title,
            thumb_media_id=self.thumb_media_id,
            show_cover_pic=1 if self.show_cover_pic else 0,
            author=self.author,
            digest=self.digest,
            content=self.content,
            url=self.url,
            content_source_url=self.content_source_url
        )

    @classmethod
    def sync(cls, app, id=None):
        if id:
            return Material.sync(app, id, Material.Type.NEWS)
        else:
            return Material.sync_type(Material.Type.NEWS, app)