from django.db import models as m
from django.utils.translation import ugettext as _

from .. import utils
from . import WeChatApp

class WeChatUser(m.Model):
    class Gender(object):
        UNKNOWN = "0"
        MALE = "1"
        FEMALE = "2"

    app = m.ForeignKey(WeChatApp, on_delete=m.CASCADE,
        related_name="users", null=False, editable=False)
    openid = m.CharField(_("openid"), max_length=36, null=False)

    nickname = m.CharField(_("nickname"), max_length=24, null=True)
    sex = m.SmallIntegerField(_("gender"), choices=utils.enum2choices(Gender), 
        null=True)
    city = m.CharField(_("city"), max_length=24, null=True)
    provice = m.CharField(_("province"), max_length=24, null=True)
    country = m.CharField(_("country"), max_length=24, null=True)
    headimgurl = m.CharField(_("avatar"), max_length=256, null=True)
    # unionid

    created = m.DateTimeField(_("created"), auto_now_add=True)
    updated = m.DateTimeField(_("updated"), auto_now=True)
    
    class Meta(object):
        ordering = ("app", "-created")
        unique_together = (("app", "openid"),)
        
    def __str__(self):
        return "{title} ({name})".format(title=self.title, name=self.name)