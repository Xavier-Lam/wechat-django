from wechat_django.rest_framework.authentication import BaseAuthentication


class MessageHandlerAuth(BaseAuthentication):
    """获取被动推送消息用户"""
    def authenticate(self, request):
        if request.method == "POST":
            openid = getattr(request.message, "source", None)
            if openid:
                app = request.wechat_app
                user, created = app.users.get_or_create(openid=openid)
                user.created = created
                return user, user.openid


class OAuthAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return 'WeChat-OAuth realm="{0}"'.format(request.wechat_app.appid)


class OAuthSessionAuthentication(OAuthAuthentication):
    """
    兼容drf的网页授权认证,包含session设置,一般使用该认证
    """
    def authenticate(self, request):
        session_key = self.get_session_key(request.wechat_app)
        openid = request.session.get(session_key)
        if openid:
            user = request.wechat_app.users.get(openid=openid)
            return user, user.openid

    def get_session_key(self, app):
        return "app:{0}:session".format(app.name)


class OAuthCodeSessionAuthentication(OAuthSessionAuthentication):
    def authenticate(self, request):
        code = request.GET["code"]
        if not code:
            return None
        scopes = request.GET["scope"]
        user = self.get_user(request.wechat_app, code, scopes)
        return user, user.openid

    def get_user(self, app, code, scopes):
        return app.auth(code, scopes)
