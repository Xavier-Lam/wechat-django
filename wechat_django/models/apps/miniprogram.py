# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from wechat_django.constants import AppType
from wechat_django.exceptions import WeChatAbilityError
from .base import ApiClientApp, InteractableApp, WeChatApp


@WeChatApp.register_apptype_cls(AppType.MINIPROGRAM)
class MiniProgramApp(ApiClientApp, InteractableApp, WeChatApp):
    """小程序"""

    def auth(self, code):
        """用code进行微信授权
        :rtype: (wechat_django.models.WeChatUser, dict)
        :raises: wechatpy.exceptions.WeChatClientException
        :raises: wechatpy.exceptions.WeChatOAuthException
        """
        if not self.abilities.api:
            raise WeChatAbilityError(WeChatAbilityError.API)

        data = self.client.code_to_session(code)
        user = self.users.upsert_by_dict(data)
        # 持久化session_key
        Session = user.sessions.model
        user.sessions.all().delete()
        user.sessions.add(Session(
            type=Session.Type.MINIPROGRAM,
            auth=dict(session_key=data["session_key"])
        ), bulk=False)
        # 移除session缓存
        try:
            del user.session
        except AttributeError:
            pass
        return user, data

    @property
    def client(self):
        return super(MiniProgramApp, self).client.wxa

    class Meta(object):
        proxy = True
