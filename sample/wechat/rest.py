#encoding: utf-8
from django.conf import settings
from django.shortcuts import redirect
from rest_framework import exceptions, generics, response, serializers as s

from wechat_django.models import WeChatUser
from wechat_django.oauth import (WeChatAuthenticated,
                                 WeChatOAuthAuthentication,
                                 WeChatOAuthViewMixin)


class UserSerializer(s.ModelSerializer):
    class Meta:
        model = WeChatUser
        fields = ("openid", "nickname")


class TestAPIView(WeChatOAuthViewMixin, generics.RetrieveAPIView,
                  generics.CreateAPIView):

    appname = settings.SAMPLEAPPNAME

    permission_classes = (WeChatAuthenticated,)
    queryset = WeChatUser.objects
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        return response.Response(request.wechat.user.nickname)

    def get_object(self):
        return self.request.wechat.user

    def handle_exception(self, exc):
        if isinstance(exc, exceptions.NotAuthenticated):
            return redirect(self.request.wechat.oauth_uri)
        return super(TestAPIView, self).handle_exception(exc)
