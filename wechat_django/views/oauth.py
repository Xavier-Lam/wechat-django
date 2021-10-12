from django.core.exceptions import SuspiciousOperation
from django.http.response import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from wechat_django import signals
from wechat_django.authentication import OAuthCodeSessionAuthentication
from wechat_django.core.view import WeChatView
from wechat_django.models.apps.mixins import OAuthApplicationMixin
from wechat_django.rest_framework.exceptions import NotAuthenticated
from wechat_django.rest_framework.permissions import IsAuthenticated
from wechat_django.sites import default_site


@default_site.register
class OAuthProxyView(WeChatView):
    authentication_classes = (OAuthCodeSessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    include_application_classes = (OAuthApplicationMixin,)
    url_pattern = r"^oauth/$"
    url_name = "oauth_proxy"

    def initialize_request(self, request, *args, **kwargs):
        if "redirect_uri" not in request.GET:
            raise SuspiciousOperation(_("Missing redirect_uri"))
        return super().initialize_request(request, *args, **kwargs)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        scopes = tuple(request.GET["scope"].split(","))
        signals.post_oauth.send_robust(request.wechat_app,
                                       user=request.user,
                                       scopes=scopes,
                                       state=request.GET["state"],
                                       request=request)

    def get(self, request, *args, **kwargs):
        # 登录用户
        for authenticator in request.authenticators:
            if isinstance(authenticator, OAuthCodeSessionAuthentication):
                sk = authenticator.get_session_key(request.wechat_app)
                request.session[sk] = request.user.openid
                break
        else:
            raise NotAuthenticated
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
            scope=request.GET.get("scope"),
            state=request.GET.get("state")
        )
        return HttpResponseRedirect(url)
