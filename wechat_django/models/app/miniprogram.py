# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils import timezone as tz

from wechat_django.constants import AppType
from wechat_django.exceptions import WeChatAbilityError
from .base import ApiClientApp, InteractableApp, WeChatApp


@WeChatApp.register_apptype_cls(AppType.MINIPROGRAM)
class MiniProgramApp(ApiClientApp, InteractableApp, WeChatApp):
    """小程序"""

    @property
    def users(self):
        from wechat_django.models.user import MiniProgramUser

        queryset = super(MiniProgramApp, self).users
        queryset.model = MiniProgramUser
        return queryset

    def auth(self, code):
        """用code进行微信授权
        :rtype: (wechat_django.models.WeChatUser, dict)
        :raises: wechatpy.exceptions.WeChatClientException
        :raises: wechatpy.exceptions.WeChatOAuthException
        """
        if not self.abilities.api:
            raise WeChatAbilityError(WeChatAbilityError.API)

        data = self.client.code_to_session(code)
        user = self.users.upsert(synced_at=tz.now(), **data)[0]
        # 持久化session_key
        user.sessions.all().delete()
        user.sessions.add(user.sessions.model(
            auth=dict(session_key=data["session_key"])
        ), bulk=False)
        # 移除session缓存
        try:
            del user.session
        except AttributeError:
            pass
        return user, data

    def _get_client(self):
        return super(MiniProgramApp, self)._get_client().wxa

    class Meta(object):
        proxy = True
