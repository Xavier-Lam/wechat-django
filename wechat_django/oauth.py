from functools import wraps
import logging

from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from six.moves.urllib.parse import parse_qsl, urlparse
from wechatpy import WeChatOAuth, WeChatOAuthException

from .models import WeChatApp, WeChatSNSScope, WeChatUser

__all__ = ("wechat_auth", )

class WeChatOAuthInfo(object):
    """附带在request上的微信对象
    
    :type app: wechat_django.models.WeChatApp
    :type user: wechat_django.models.WeChatUser
    :attribute redirect_uri: 授权后重定向回的地址
    :attribute oauth_uri: 授权地址
    :attribute state: 授权携带的state
    :attribute scope: 授权的scope
    """
    app = None
    user = None
    redirect_uri = None
    state = ""
    scope = WeChatSNSScope.BASE

    @property
    def oauth_uri(self):
        return self.app.oauth.authorize_url(
            self.redirect_uri,
            self.scope,
            self.state
        )

    def __init__(self, **kwargs):
        for k, v in kwargs.values():
            setattr(self, k, v)

    def __str__(self):
        return "WeChatOuathInfo: " + "\t".join(
            "{k}: {v}".format(k=attr, v=getattr(self, k, None))
            for attr in 
            ("app", "user", "redirect", "oauth_uri", "state", "scope")
        )

def wechat_auth(appname, scope=WeChatSNSScope.BASE, redirect_uri=None,
    required=True, response=None, state=""):
    """微信网页授权
    :param appname: WeChatApp的name
    :param scope: 默认WeChatSNSScope.BASE, 可选WeChatSNSScope.USERINFO
    :param redirect_uri: 未授权时的重定向地址 当未设置response时将自动执行授权
                         当ajax请求时默认取referrer 否则取当前地址
                         注意 请不要在地址上带有code及state参数 否则可能引发问题
    :param state: 授权时需要携带的state
    :param required: 真值必须授权 否则不授权亦可继续访问(只检查session)
    :param response: 未授权的返回 接受一个
    :type response: django.http.response.HttpResponse
                    or Callable[
                        [
                            django.http.request.HttpRequest,
                            *args,
                            **kwargs
                        ], 
                        django.http.response.HttpResponse
                    ]
    """
    assert (response is None or callable(response) 
        or isinstance(response, HttpResponse)), "incorrect response"
    assert scope in (WeChatSNSScope.BASE, WeChatSNSScope.USERINFO), \
        "incorrect scope"
    logger = _logger(appname)

    def decorator(func):
        @wraps
        def decorated_func(request, *args, **kwargs):
            """:type request: django.http.request.HttpRequest"""
            # 优先检查session
            session_key = "wechat_{0}_user".format(appname)
            openid = request.get_signed_cookie(session_key, None)

            # 未设置redirect_uri ajax取referrer 否则取当前地址
            if not redirect_uri:
                full_url = request.build_absolute_uri()
                redirect_uri = ((request.META.get("HTTP_REFERER") or full_url)
                    if request.is_ajax() else full_url)

            request.wechat = wechat = WeChatOAuthInfo(
                redirect_uri=redirect_uri, state=state, scope=scope)
            try:
                wechat.app = app = WeChatApp.get_by_name(appname)
            except WeChatApp.DoesNotExist:
                logger.warning("wechat app not exists: {0}".format(appname))
                return HttpResponseNotFound()     

            if required and not openid:
                # 设定了response优先返回response
                if response:
                    if callable(response):
                        return response(request, *args, **kwargs)
                    return response

                code = get_request_code(request)
                # 根据code获取用户信息
                try:
                    user_dict = code and auth_by_code(app, code, scope)
                    openid = user_dict.get("openid")
                    # 更新user_dict
                    WeChatUser.upsert_by_oauth(app, user_dict)
                except WeChatOAuthException:
                    logger.warning("auth code failed: {0}".format(dict(
                        info=wechat,
                        code=code
                    )), exc_info=True)
                except AssertionError:
                    logger.error("incorrect auth response: {0}".format(dict(
                        info=wechat,
                        user_dict=user_dict
                    )), exc_info=True)
                else:
                    # 用当前url的state替换传入的state
                    wechat.state = request.GET.get("state", "")
                
                if required and not openid:
                    # 最后执行重定向授权
                    return redirect(wechat.oauth_uri)

            if openid:
                wechat.user = WeChatUser.get_by_openid(app, openid)

            rv = func(request, *args, **kwargs)
            openid and rv.set_signed_cookie(session_key, openid)
            return rv

        return decorated_func
    return decorator

def get_request_code(request):
    if request.is_ajax():
        try:
            referrer = request.META["HTTP_REFERER"]
            query = dict(parse_qsl(urlparse(referrer).query))
            code = query.get("code")
        except:
            code = None
    else:
        code = request.GET.get("code")
    return code

def auth_by_code(app, code, scope):
    # 检查code有效性
    data = app.oauth.fetch_access_token(code)
    
    if scope == WeChatSNSScope.USERINFO:
        # 同步数据
        try:
            user_info = app.oauth.get_user_info()
            data.update(user_info)
        except WeChatOAuthException:
            _logger(app.name).warning("get userinfo failed", exc_info=True)
    
    return data

def _logger(appname):
    return logging.getLogger("wechat:oauth:{0}".format(appname))