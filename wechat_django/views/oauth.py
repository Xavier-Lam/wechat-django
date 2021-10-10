from django.http.response import HttpResponseRedirect

from wechat_django import signals
from wechat_django.authentication import OAuthCodeSessionAuthentication
from wechat_django.core.view import WeChatView
from wechat_django.models.apps.mixins import OAuthApplicationMixin
from wechat_django.rest_framework.permissions import IsAuthenticated
from wechat_django.sites import default_site


@default_site.register
class PostOAuthView(WeChatView):
    authentication_classes = (OAuthCodeSessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    include_application_classes = (OAuthApplicationMixin,)
    url_pattern = r"^oauth/$"
    url_name = "post_oauth"

    def initialize_request(self, request, *args, **kwargs):
        request.GET["redirect_uri"]
        return super().initialize_request(request, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        signals.post_oauth.send(request.wechat_app,
                                user=request.user,
                                scopes=request.GET["scope"].split(","),
                                state=request.GET["state"],
                                request=request)

    def get(self, request, *args, **kwargs):
        # 登录用户
        request.session["session_key"] = request.user.openid
        return self.make_response(redirect_uri=request.GET["redirect_uri"],
                                  scope=request.GET["scope"],
                                  state=request.GET["state"],
                                  request=request)

    def make_response(self, redirect_uri, scope, state, request):
        return HttpResponseRedirect(redirect_uri)

    def handle_exception(self, exc):
        # 原则上所有异常都应该重新授权
        request = self.request
        app = request.wechat_app
        url = app.build_oauth_url(
            request,
            next=request.GET["redirect_uri"],
            scopes=request.GET.get("scope"),
            state=request.GET.get("state")
        )
        return HttpResponseRedirect(url)
