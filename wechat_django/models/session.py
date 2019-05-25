# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models as m
from django.utils.translation import ugettext_lazy as _
import hashlib
import json
from jsonfield import JSONField

from wechatpy.crypto import WeChatWxaCrypto
from wechatpy.exceptions import InvalidSignatureException

from . import WeChatModel, WeChatUser


class Session(WeChatModel):
    class Type(object):
        MINIPROGRAM = 1

    user = m.ForeignKey(
        WeChatUser, on_delete=m.CASCADE, related_name="sessions", null=False)
    type = m.PositiveSmallIntegerField()
    auth = JSONField(default={})

    created_at = m.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = m.DateTimeField(_("updated at"), auto_now=True)

    @property
    def app(self):
        return self.user.app

    @property
    def app_id(self):
        return self.user.app_id

    @property
    def session_key(self):
        return self.auth.get("session_key")

    def decrypt_message(self, msg, iv):
        """
        :raises: ValueError
        """
        crypto = WeChatWxaCrypto(self.session_key, iv, self.app.appid)
        return crypto.decrypt_message(msg)

    def validate_message(self, msg, sign):
        """
        :raises: wechatpy.exceptions.InvalidSignatureException
        """
        str_to_sign = (msg + self.session_key).encode()
        server_sign = hashlib.sha1(str_to_sign).hexdigest()
        if server_sign != sign:
            raise InvalidSignatureException()
        return json.loads(msg)

    def __str__(self):
        return "session_key: {0}".format(self.session_key)
