# 网页开发

- [服务号网页授权](#%e6%9c%8d%e5%8a%a1%e5%8f%b7%e7%bd%91%e9%a1%b5%e6%8e%88%e6%9d%83)
- [jssdk](#jssdk)
- [开放平台网站应用](#%e5%bc%80%e6%94%be%e5%b9%b3%e5%8f%b0%e7%bd%91%e7%ab%99%e5%ba%94%e7%94%a8)

## 服务号网页授权
可通过`wechat_django.oauth.wechat_auth`装饰器进行网页授权,授权后,request将被附上一个名为wechat的`wechat_django.oauth.WeChatOAuthInfo` 对象,可通过 request.wechat.user 拿到`wechat_django.models.Public`实例,通过 request.wechat.app 拿到`wechat_django.models.ServiceApp`实例,以下是一个基本示例

    from wechat_django import wechat_auth

    @wechat_auth("your_app_name")
    def your_view(request, *args, **kwargs):
        """:type request: wechat_django.requests.WeChatOAuthRequest"""
        user = request.wechat.user

对于默认重定向行为不满意的,可以自定义response,具体的参数说明参见`wechat_django.oauth.wechat_auth`装饰器的docstring

对于class based view,可继承`wechat_django.oauth.WeChatOAuthView`类,具体参见代码

## jssdk
首先你需要自行引入微信的js文件

    <script src="//res.wx.qq.com/open/js/jweixin-1.4.0.js"></script>

在模板文件中加入

    <script src="{% url 'wechat_django:jsconfig' 'debug' %}?jsApiList=onMenuShareTimeline,onMenuShareAppMessage&debug=1"></script>

如果你没有使用模板,默认地址应该是

    <script src="/wechat/{{yourappname}}/wx.jsconfig.js?jsApiList=onMenuShareTimeline,onMenuShareAppMessage&debug=1"></script>

其中,jsApiList参数传入需要使用的JS接口列表,debug如填写且settings.py的DEBUG为真值,则会配置调试模式.

以下是上述示例js的输出结果:

    wx.config(JSON.parse('{"debug": true, "appId": "appId", "timestamp": 1575299361, "nonceStr": "95b992c5263b4c6689fc7fdcb6f1ddc8", "signature": "8cb73b3536ee3b787f63d6e6cf9ddd1f06afd94a", "jsApiList": ["onMenuShareTimeline", "onMenuShareAppMessage"]}'));

## 开放平台网站应用
在后台配置网站应用后

    app = WeChatApp.objects.get_by_name("your webapp name")
    url = app.oauth.qrconnect_url("https://www.zhihu.com/oauth/callback/wechat?action=login&from=", 1234567)

用户授权成功回调以后,将在回调页面拿到code和state,可通过`app.oauth`拿到用户对象及接口响应

    def index(request):
        code = request.GET["code"]
        state = request.GET["state"]
        user, data = app.oauth(code)