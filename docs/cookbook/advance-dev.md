# 进阶开发

- [使用自定义请求客户端](#%e4%bd%bf%e7%94%a8%e8%87%aa%e5%ae%9a%e4%b9%89%e8%af%b7%e6%b1%82%e5%ae%a2%e6%88%b7%e7%ab%af)
- [使用WeChatUser作为用户登录](#%e4%bd%bf%e7%94%a8wechatuser%e4%bd%9c%e4%b8%ba%e7%94%a8%e6%88%b7%e7%99%bb%e5%bd%95)

## 使用自定义请求客户端
在开发过程中,默认的请求客户端可能不能满足开发需求(诸如对接的微信api非微信官方api,而是第三方微信api),需要修改model中默认的请求客户端.这种情况下,我们通过代理模型来实现.

1. 首先,我们定义自己的请求客户端

        from wechat_django.client import WeChatClient

        class CustomWeChatClient(WeChatClient):
            def _fetch_access_token(self, url, params):
                return dict(
                    access_token="1234567",
                    expires_in=60*30
                )

2. 实现一个`wechat_django.models.WeChatApp`的代理类,复写_get_client方法

        from wechat_django.models import WeChatApp

        class CustomWeChatApp(WeChatApp):
            def _get_client(self):
                return CustomWeChatClient(self)

3. 使用代理类来获取app实例

        app = CustomWeChatApp.objects.get_by_name("111")

除了client外,修改`wechat_django.models.WeChatApp.oauth`可通过复写`wechat_django.models.WeChatApp._get_oauth`方法实现,修改`wechat_django.pay.models.WeChatPay.client`可通过复写`wechat_django.pay.models.WeChatPay._get_client`实现.


## 使用WeChatUser作为用户登录
1. 由于`wechat_django.models.WeChatUser`没有last_login字段,需要在你的appconfig中的ready方法加入以下代码防止django在自动更新update_last_login时报错

        from django.contrib.auth.models import update_last_login
        from django.contrib.auth.signals import user_logged_in

        user_logged_in.disconnect(update_last_login, dispatch_uid='update_last_login')

2. 使用`django.contrib.auth.login`登录
