# ChangeLog

breaking changes以:exclamation:开头标注
- [0.3.2](#032)
- [0.3.1](#031)
- [0.3.0](#030)
- [0.2.5](#025)
- [0.2.4](#024)
- [0.2.2](#022)
- [0.2.0](#020)
- [0.1.0](#010)

## 0.3.2
* 重构站点,视图,全部继承django-rest-framework风格的APIView

## 0.3.1
* 微信网页授权对django-rest-framework进行兼容
* [自定义消息处理规则](docs/cookbook/messages.md#自定义处理规则)
* 接收到微信消息与处理完成微信消息信号
* 移除settings中的`WECHAT_WECHATCLIENT`,`WECHAT_OAUTHCLIENT`,`WECHAT_PAYCLIENT`选项,请开发者[通过继承代理类实现](docs/cookbook/advance-dev.md#使用自定义请求客户端)

## 0.3.0
* 微信支付client
* 统一下单订单管理,回调及订单状态变更信号
* :exclamation: 小程序的client由`wechat_django.client.WeChatClient`变更为`wechatpy.client.api.WeChatWxa`
* :exclamation: 数个配置项更改
* 站点及模型代码重构
* 要求wechatpy最低版本1.8.3

## 0.2.5
* [模板消息](docs/cookbook/messages.md#模板消息)

## 0.2.4
* 小程序授权及验证/解密信息
* 要求wechatpy最低版本1.8.2

## 0.2.2
* 重构控制台路由及相关代码,引入[django-object-tool](https://github.com/Xavier-Lam/django-object-tool)
* 可在控制台配置应用的accesstoken及oauth_url,以便接入第三方服务

## 0.2.0
* 重构代码,修改站点url注册方式,修改部分低级api
* 用户标签管理功能
* 要求wechatpy最低版本1.8.0

## 0.1.0
* 公众号管理及基本用法封装
* 用户,自动回复,菜单,永久素材,图文的基本管理
* 微信网页授权
* 后台权限