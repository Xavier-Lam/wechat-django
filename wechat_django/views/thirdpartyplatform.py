from urllib.parse import urlencode
from django.http.response import HttpResponse, HttpResponseRedirect

from django.utils.translation import ugettext_lazy as _

from wechat_django.core.view import WeChatView
from wechat_django.models.apps import ThirdPartyPlatform


class ThirdPartyPlatformAuth(WeChatView):
    include_application_classes = (ThirdPartyPlatform,)
    url_pattern = r"^thirdpartyplatformauth/$"
    url_name = "thirdpartyplatform_auth"

    def get(self, request, *args, **kwargs):
        if "auth_code" in request.GET:
            wechat_app = self.post_auth(request)
            return self.render_success(request, wechat_app)

        return self.pre_auth(request)

    def pre_auth(self, request):
        redirect_url = self.create_url(request)
        return HttpResponseRedirect(redirect_url)

    def post_auth(self, request):
        code = request.GET["auth_code"]
        request.wechat_app.query_auth(code)

    def create_url(self, request):
        app = request.wechat_app
        pre_auth_info = app.client.create_preauthcode()
        data = {
            "component_appid": app.appid,
            "pre_auth_code": pre_auth_info["pre_auth_code"]
        }
        if "micromessenger" in request.META.get("HTTP_USER_AGENT", ""):
            base_url = "https://mp.weixin.qq.com/safe/bindcomponent"
        else:
            base_url = "https://mp.weixin.qq.com/cgi-bin/componentloginpage"
            data.update({
                "action": "bindcomponent",
                "auth_type": 3,
                "no_scan": 1
            })
        query = request.GET.copy()
        data["auth_type"] = query.pop("auth_type", "")
        data["biz_appid"] = query.pop("biz_appid", "")
        data["redirect_uri"] = request.build_absolute_uri(self.get_url(app))
        if query:
            data["redirect_uri"] += "?" + urlencode(query)
        return "{0}?{1}".format(base_url, urlencode(data))

    def render_success(self, request, wechat_app):
        return HttpResponse(_("Success"))
