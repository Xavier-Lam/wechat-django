# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.http.response import Http404


class WeChatInfo(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    @property
    def appname(self):
        return self._appname

    @property
    def app(self):
        """
        :rtype: wechat_django.models.WeChatApp
        """
        if not hasattr(self, "_app"):
            try:
                self._app = self.app_queryset.get_by_name(self.appname)
            except self.app_queryset.model.DoesNotExist:
                raise Http404()
        return self._app

    @property
    def request(self):
        """
        :rtype: django.http.request.HttpRequest
        """
        return self._request

    @property
    def openid(self):
        if not hasattr(self, "_openid"):
            raise NotImplementedError()
        return self._openid

    @property
    def user(self):
        """
        :rtype: wechat_django.models.WeChatUser
        """
        if not hasattr(self, "_user"):
            self._user = self.app.user_by_openid(self.openid)
        return self._user

    @property
    def local_user(self):
        """
        不从微信服务器重新同步用户
        :rtype: wechat_django.models.WeChatUser
        """
        if not hasattr(self, "_user") and not hasattr(self, "_local_user"):
            self._local_user = self.app.user_by_openid(
                self.openid, ignore_errors=True, sync_user=False)
        return self._user if hasattr(self, "_user") else self._local_user

    _app_queryset = None

    @property
    def app_queryset(self):
        from wechat_django.models import WeChatApp

        if not self._app_queryset:
            self._app_queryset = WeChatApp.objects
        return self._app_queryset

    @classmethod
    def from_wechat_info(cls, wechat_info):
        """
        :type wechat_info: wechat_django.models.WeChatInfo
        """
        properties = ("_app", "_appname", "_app_queryset", "_local_user",
                      "_openid", "_request", "_user")
        kwargs = {
            p: getattr(wechat_info, p)
            for p in properties if hasattr(wechat_info, p)
        }
        return cls(**kwargs)
