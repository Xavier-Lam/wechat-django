from functools import wraps

from django.http.response import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from six.moves.urllib.parse import parse_qsl, urlparse
from wechatpy import WeChatOAuth, WeChatOAuthException

from .models import WeChatApp, WeChatSNSScope, WeChatUser

__all__ = ("wechat_auth", )

def wechat_auth(app_name, scope=WeChatSNSScope.BASE, redirect_uri=None,
    required=True, response=None, state=""):
    """微信网页授权
    :param app_name: WeChatApp的name
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
    # TODO: 检查callable response

    def decorator(func):
        @wraps
        def decorated_func(request, *args, **kwargs):
            """:type request: django.http.request.HttpRequest"""
            # 优先检查session
            session_key = "wechat_{0}_user".format(app_name)
            openid = request.get_signed_cookie(session_key, None)

            try:
                request.wechat_app = app = WeChatApp.get_by_name(app_name)
            except WeChatApp.DoesNotExist:
                # TODO: 日志
                return HttpResponseNotFound()

            if required and not openid:
                # 设定了response优先返回response
                if response:
                    if callable(response):
                        return response(request, *args, **kwargs)
                    return response
                
                # 未设置redirect_uri ajax取referrer 否则取当前地址
                if not redirect_uri:
                    full_url = request.build_absolute_uri()
                    redirect_uri = ((request.META.get("HTTP_REFERER") or full_url)
                        if request.is_ajax() else full_url)

                client = WeChatOAuth(app.appid, app.appsecret, 
                    redirect_uri=redirect_uri, scope=scope, state=state)
                code = _get_code_from_request(request)
                if code:
                    # 检查code有效性
                    try:
                        data = client.fetch_access_token(code)
                        openid = data.get("openid")
                    except WeChatOAuthException:
                        # TODO: 日志
                        pass
                    
                    if openid:
                        # TODO: 将数据写入
                        if scope == WeChatSNSScope.USERINFO:
                            # TODO: 同步数据
                            pass
                
                if required and not openid:
                    # 最后执行重定向授权
                    return redirect(redirect_uri)

                if openid:
                    request.wechat_user = WeChatUser.get_by_openid(app, openid)

            # 执行 
            rv = func(request, *args, **kwargs)
            openid and rv.set_signed_cookie(session_key, openid)
            return rv

        return decorated_func
    return decorator

def _get_code_from_request(request):
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

def _request_for_auth(request, redirect_uri=None, 
    scope=WeChatSNSScope.BASE, state=""):
    client = WeChatOAuth(request.wechat_app.appid, 
        request.wechat_app.appsecret, redirect_uri, scope)
    