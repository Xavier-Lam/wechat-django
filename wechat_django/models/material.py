import re

from django.db import models as m, transaction
from django.utils.translation import ugettext as _

from .. import utils
from . import WechatApp

class Material(m.Model):
    class Type(object):
        IMAGE = "image"
        VIDEO = "video"
        # NEWS = "news"
        VOICE = "voice"

    app = m.ForeignKey(WechatApp, on_delete=m.CASCADE,
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

    @classmethod
    def sync(cls, app):
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
        # 对于图文 单独处理
        while True:
            data = app.client.material.batchget(
                media_type=type,
                offset=offset,
                count=count
            )
            updates.extend(map(lambda o: Material(app=app, **o), data["item"]))
            if data["total_count"] <= offset + count:
                break
            offset += count
        # TODO: 优化为删除被删除的 更新或新增获取的
        cls.objects.filter(app=app, type=type).delete()
        cls.objects.bulk_create(updates)
        return updates

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
            # TODO: 默认文件名
            filename = None
        
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
