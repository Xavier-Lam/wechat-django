from django.core.exceptions import SuspiciousOperation
from django.http.response import HttpResponseRedirect
from django.utils.module_loading import import_string
from django.utils.translation import ugettext_lazy as _

from wechat_django import signals
from wechat_django.authentication import OAuthCodeSessionAuthentication
from wechat_django.core import settings
from wechat_django.core.view import WeChatView
from wechat_django.models.apps.mixins import OAuthApplicationMixin
from wechat_django.rest_framework.permissions import IsAuthenticated
from wechat_django.sites import default_site


@default_site.register
class OAuthProxyView(WeChatView):
    authentication_classes = (OAuthCodeSessionAuthentication,)
    permission_classes = (IsAuthenticated,)

    include_application_classes = (OAuthApplicationMixin,)
    url_pattern = r"^oauth/$"
    url_name = "oauth_proxy"

    def __init__(self, **kwargs):
        self._oauth_login = import_string(settings.get("OAUTH_LOGIN_HANDLER"))
        super().__init__(**kwargs)

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
        return self.oauth_login(request.user,
                                redirect_uri=request.GET["redirect_uri"],
                                scope=request.GET["scope"],
                                state=request.GET["state"],
                                request=request)

    def oauth_login(self, user, redirect_uri, scope, state, request):
        return self._oauth_login(user, redirect_uri, scope, state, request)

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
