import mimetypes
import re

from django.db import models as m, transaction
from django.utils.translation import ugettext as _

from .. import utils
from . import WeChatApp

class Material(m.Model):
    class Type(object):
        IMAGE = "image"
        VIDEO = "video"
        NEWS = "news"
        VOICE = "voice"

    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE,
        related_name="materials")
    type = m.CharField(_("type"), max_length=5,
        choices=(utils.enum2choices(Type)))
    media_id = m.CharField(_("media_id"), max_length=64)
    name = m.CharField(_("name"), max_length=64, blank=True, null=True)
    url = m.CharField(_("url"), max_length=512, editable=False, null=True)
    update_time = m.IntegerField(_("update time"), editable=False, 
        null=True)

    comment = m.TextField(_("comment"), blank=True)
    
    created = m.DateTimeField(_("created"), auto_now_add=True)
    updated = m.DateTimeField(_("updated"), auto_now=True)

    class Meta(object):
        unique_together = (("app", "media_id"),)
        ordering = ("app", "-update_time")

    @classmethod
    def get_by_media(cls, app, media_id):
        return cls.objects.get(app=app, media_id=media_id)

    @classmethod
    def sync(cls, app, id=None, type=None):
        if id:
            if type not in (cls.Type.NEWS, cls.Type.VIDEO):
                raise NotImplementedError()
            data = app.client.material.get_raw(id)
            return cls.create(app=app, type=type, media_id=id, **data)
        else:
            updated = []
            for type, _ in utils.enum2choices(cls.Type):
                with transaction.atomic():
                    updates = cls.sync_type(type, app)
                    updated.extend(updates)
            return updated

    @classmethod
    def sync_type(cls, type, app):
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
        return [cls.create(app=app, type=type, **item) for item in updates]

    @classmethod
    def as_permenant(cls, media_id, app, save=True):
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

        try:    
            disposition = resp.headers["Content-Disposition"]
            filename = re.findall(r'filename="(.+?)"', disposition)[0]
        except:
            # 默认文件名
            ext = mimetypes.guess_extension(content_type)
            filename = (media_id + ext) if ext else media_id
        
        return cls.upload_permenant((filename, resp.content), type, app, save)

    @classmethod
    def upload_permenant(cls, file, type, app, save=True):
        # 上传文件
        data = app.client.material.add(type, file)
        media_id = data["media_id"]
        if save:
            rv = cls(type=type, media_id=media_id, url=data.get("url"))
            return rv.save()
        else:
            return media_id

    @classmethod
    def create(cls, app, type=None, **kwargs):
        from . import Article
        if type is None:
            raise NotImplementedError()
        if type == cls.Type.NEWS:
            cls.create_news(app, **kwargs)
        else:
            media_id = kwargs["media_id"]
            allowed_keys = list(map(lambda o: o.name, cls._meta.fields))
            if type == cls.Type.VIDEO and "url" not in kwargs:
                data = app.client.material.get(media_id)
                kwargs["url"] = data.get("down_url")
            
            kwargs = {key: kwargs[key] for key in allowed_keys if key in kwargs}
            record = dict(app=app, type=type, **kwargs)
            return cls.objects.update_or_create(defaults=record, 
                app=app, type=type, media_id=media_id)[0]

    @classmethod
    def create_news(cls, app, **kwargs):
        from . import Article
        # 插入media
        query = dict(app=app, media_id=kwargs["media_id"])
        record = dict(type=cls.Type.NEWS, update_time=kwargs["update_time"])
        record.update(query)
        news, created = cls.objects.update_or_create(record, **query)
        if not created:
            # 移除所有article重新插入
            news.articles.all().delete()

        articles = (kwargs.get("content") or kwargs)["news_item"]
        fields = list(map(lambda o: o.name, Article._meta.fields))
        Article.objects.bulk_create([
            Article(
                index=idx, 
                material=news,
                _thumb_url=article.get("thumb_url"),
                **{k: v for k, v in article.items() if k in fields} # 过滤article fields
            )
            for idx, article in enumerate(articles)
        ])
        return news

    def delete(self, *args, **kwargs):
        self.app.client.material.delete(self.media_id)
        rv = super().delete(*args, **kwargs)
        return rv

    def __str__(self):
        media = "{type}:{media_id}".format(type=self.type, media_id=self.media_id)
        return "{0} ({1})".format(self.comment, media) if self.comment else media