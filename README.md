# WeChat-Django

[![PyPI](https://img.shields.io/pypi/v/wechat-django.svg)](https://pypi.org/project/wechat-django)
[![Build Status](https://travis-ci.org/Xavier-Lam/wechat-django.svg?branch=master)](https://travis-ci.org/Xavier-Lam/wechat-django)

**WeChat-Django**旨在为接入微信公众平台的django开发者提供便捷的微信及微信支付功能封装及基本的[**后台管理支持**](docs/admin.md).

项目官方地址: https://github.com/Xavier-Lam/wechat-django

本拓展基于[wechatpy](https://github.com/jxtech/wechatpy) ,支持的最低django版本为1.11. WeChat-Django只是一个预览版本,可能存在较多bug并且有api及数据结构变更可能.

目录
======
- [功能](#%e5%8a%9f%e8%83%bd)
- [安装及配置](#%e5%ae%89%e8%a3%85%e5%8f%8a%e9%85%8d%e7%bd%ae)
  - [初次安装](#%e5%88%9d%e6%ac%a1%e5%ae%89%e8%a3%85)
  - [直接加入项目](#%e7%9b%b4%e6%8e%a5%e5%8a%a0%e5%85%a5%e9%a1%b9%e7%9b%ae)
  - [更新](#%e6%9b%b4%e6%96%b0)
  - [配置](#%e9%85%8d%e7%bd%ae)
  - [日志](#%e6%97%a5%e5%bf%97)
  - [注意事项](#%e6%b3%a8%e6%84%8f%e4%ba%8b%e9%a1%b9)
- [部分功能使用说明](#%e9%83%a8%e5%88%86%e5%8a%9f%e8%83%bd%e4%bd%bf%e7%94%a8%e8%af%b4%e6%98%8e)
  - [网页授权](#%e7%bd%91%e9%a1%b5%e6%8e%88%e6%9d%83)
  - [小程序授权](#%e5%b0%8f%e7%a8%8b%e5%ba%8f%e6%8e%88%e6%9d%83)
    - [小程序信息加解密及用户数据更新](#%e5%b0%8f%e7%a8%8b%e5%ba%8f%e4%bf%a1%e6%81%af%e5%8a%a0%e8%a7%a3%e5%af%86%e5%8f%8a%e7%94%a8%e6%88%b7%e6%95%b0%e6%8d%ae%e6%9b%b4%e6%96%b0)
  - [主动调用微信api](#%e4%b8%bb%e5%8a%a8%e8%b0%83%e7%94%a8%e5%be%ae%e4%bf%a1api)
  - [自定义微信回复](#%e8%87%aa%e5%ae%9a%e4%b9%89%e5%be%ae%e4%bf%a1%e5%9b%9e%e5%a4%8d)
  - [微信支付](#%e5%be%ae%e4%bf%a1%e6%94%af%e4%bb%98)
    - [统一下单](#%e7%bb%9f%e4%b8%80%e4%b8%8b%e5%8d%95)
    - [订单更新(回调)通知](#%e8%ae%a2%e5%8d%95%e6%9b%b4%e6%96%b0%e5%9b%9e%e8%b0%83%e9%80%9a%e7%9f%a5)
  - [django-rest-framework](#django-rest-framework)
- [后台使用简介](#%e5%90%8e%e5%8f%b0%e4%bd%bf%e7%94%a8%e7%ae%80%e4%bb%8b)
- [示例项目](#%e7%a4%ba%e4%be%8b%e9%a1%b9%e7%9b%ae)
- [TODOS:](#todos)
  - [计划的功能](#%e8%ae%a1%e5%88%92%e7%9a%84%e5%8a%9f%e8%83%bd)
  - [已知bugs](#%e5%b7%b2%e7%9f%a5bugs)
- [Changelog](#changelog)


## 功能
* 公众号管理
* 同步用户及用户查看,备注,用户标签管理
* 菜单同步,查看及发布
* 同步公众号自动回复,管理自动回复,转发和自定义自动回复业务,接收消息日志
* 模板消息模板的同步及发送
* 永久素材,图文的同步及查看
* 微信网页授权
* 主动调用微信api封装
* 微信支付api封装
* 微信支付订单管理及信号
* 后台权限管理

## 安装及配置
### 初次安装
1. 运行**pip install wechat-django[cryptography]** 或 **pip install wechat-django[pycrypto]** 安装
2. 在settings.py的**INSTALLED_APPS中添加wechat_django**
3. 运行**manage.py migrate wechat_django** 来更新数据库结构
4. 在urls.py 中引入wechat_django.sites.wechat.urls, 将其配置到urlpatterns中

至此,您已可以开始轻松使用wechat_django.项目尚未提供具体的使用文档,如需客制化需求,烦请先阅读代码

### 直接加入项目
想使用最新特性或是自行编辑代码,可clone本项目后,采用pip install -e 直接安装到你的django项目目录

### 更新
1. 运行**pip install -U wechat-django**
2. 运行**python manage.py migrate** 来更新数据库结构

### 配置
一般而言,默认配置足以满足需求

| 参数名 | 默认值 | 说明 |
| --- | --- | --- |
| WECHAT_SITE_HOST | None | 用于接收微信回调的默认域名 |
| WECHAT_SITE_HTTPS | True | 接收微信回调域名是否是https |
| WECHAT_PATCHADMINSITE | True | 是否将django默认的adminsite替换为wechat_django默认的adminsite, 默认替换 |
| WECHAT_SESSIONSTORAGE | "django.core.cache.cache" | 用于存储微信accesstoken等数据的[`wechatpy.session.SessionStorage`](https://wechatpy.readthedocs.io/zh_CN/master/quickstart.html#id10) 对象,或接收 `wechat_django.models.WeChatApp` 对象并生成其实例的工厂方法 |
| WECHAT_MESSAGETIMEOFFSET | 180 | 微信请求消息时,timestamp与服务器时间差超过该值的请求将被抛弃 |
| WECHAT_MESSAGENOREPEATNONCE | True | 是否对微信消息防重放检查 默认检查 |

### 日志
| logger | 说明 |
| --- | --- |
| wechat.admin.{appname} | admin异常日志 最低级别warning |
| wechat.api.{appname} | api日志 最低级别debug |
| wechat.handler.{appname} | 消息处理日志 最低级别debug |
| wechat.oauth.{appname} | 网页授权异常日志 最低级别warning |
| wechat.site.{appname} | 站点view异常日志(如素材代理) 最低级别warning |

### 注意事项
* 框架默认采用django的cache管理accesstoken,如果有多个进程,或是多台机器部署,请确保所有worker使用公用cache以免造成token争用,如果希望不使用django的cache管理accesstoken,可以在配置项中定义SessionStorage
* 请确保在https环境下部署,否则有secretkey泄露的风险

## 部分功能使用说明
### 网页授权
可通过`wechat_django.oauth.wechat_auth`装饰器进行网页授权,授权后,request将被附上一个名为wechat的`wechat_django.oauth.WeChatOAuthInfo` 对象,可通过 request.wechat.user 拿到`wechat_django.models.WeChatUser`实例,通过 request.wechat.app 拿到`wechat_django.models.WeChatApp`实例,以下是一个基本示例

    from wechat_django import wechat_auth

    @wechat_auth("your_app_name")
    def your_view(request, *args, **kwargs):
        """:type request: wechat_django.requests.WeChatOAuthRequest"""
        user = request.wechat.user

对于默认重定向行为不满意的,可以自定义response,具体的参数说明参见`wechat_django.oauth.wechat_auth`装饰器的docstring

对于class based view,可继承`wechat_django.oauth.WeChatOAuthView`类,具体参见代码


### 小程序授权
通过`wechat_django.models.WeChatApp.auth`进行授权,输入客户端传来的code, 输出一个用户对象以及原始响应.这个方法只能拿到用户的openid与unionid.

    from wechat_django.models import WeChatApp
    app = WeChatApp.objects.get_by_name("your app name")
    user, data = app.auth(code)

对于授权后得到的session_key,框架会持久化至数据库,此后可以通过调用`wechat_django.models.WeChatUser.session`来执行相关操作.

auth方法同样适用于网页授权,第二个参数填写网页授权的scope,默认base.

#### 小程序信息加解密及用户数据更新
对于已经进行过小程序授权并且session_key尚未过期的用户,可以使用`wechat_django.models.Session.decrypt_message`来解密客户端传来的敏感数据

    encrypted_data = ""
    iv = ""
    try:
        data = user.session.decrypt_message(
            encrypted_data, iv)
    except ValueError:
        pass # 无法正确解密数据 session_key可能过期了


亦可使用`wechat_django.models.Session.validate_message`来校验客户端传来的数据

    from wechatpy.exceptions import InvalidSignatureException

    signature = ""
    raw_data = ""
    try:
        data = user.session.validate_message(raw_data, signature)
    except InvalidSignatureException:
        pass # 签名错误 session_key可能过期了

客户端调用`wx.getUserInfo`,可将rawData与signature传递至后端,后端通过调用`wechat_django.models.Session.validate_message`与`wechat_django.models.User.update`来更新用户信息

    from django.http.response import HttpResponse
    from wechatpy.exceptions import InvalidSignatureException

    signature = request.POST["signature"]
    raw_data = request.POST["rawData"]
    
    try:
        data = user.session.validate_message(raw_data, signature)
    except InvalidSignatureException:
        return HttpResponse(status=401)

使用update方法更新用户数据

    user.update(data)

### 主动调用微信api
    from wechat_django.models import WeChatApp
    app = WeChatApp.get_by_name("your app name")
    data = app.client.user.get_followers()

具体client的使用方式,请移步[wechatpy文档](https://wechatpy.readthedocs.io/zh_CN/master/client/index.html)

### 自定义微信回复
在后台配置自定义回复,填写自定义回复处理代码的路径,代码须由 `wechat_django.handler.message_handler` 装饰对应的方法接收一个 `wechat_django.models.WeChatMessageInfo` 对象,返回字符串或一个 [`wechatpy.replies.BaseReply`](https://wechatpy.readthedocs.io/zh_CN/master/replies.html) 对象

    from wechat_django import message_handler

    @message_handler
    def custom_business(message):
        """
        :type message: wechat_django.models.WeChatMessageInfo
        """
        user = message.user
        msg = message.message
        text = "hello, {0}! we received a {1} message.".format(
            user, msg.type)
        return TextReply(content=text.encode())

### 微信支付
使用微信支付,需要在INSTALLED_APP的`wechat_django`后添加`wechat_django.pay`.

#### 统一下单

    from wechat_django.models import WeChatApp
    app = WeChatApp.objects.get_by_name("your app name")
    order = app.pay.create_order(
        user="user-instance", body="body", total_fee=1,
        out_trade_no="***debug***20190613001") # 也可以用openid="openid"代替user参数
    prepay = order.prepay(request)

将jsapi参数交给前端

    jsapi_params = order.jsapi_params(prepay["prepay_id"])

主动查询订单状态

    order.sync()

#### 订单更新(回调)通知

当订单更新时,会发出`wechat_django.pay.signals.order_updated`信号,sender为订单`wechat_django.utils.func.Static("{appname}.{payname}")`.信号提供4个变量

| 变量 | 说明 |
| --- | --- |
| result | 订单结果(`wechat_django.pay.models.UnifiedOrderResult`) |
| order | 更新的订单(`wechat_django.pay.models.UnifiedOrder`) |
| state | 订单状态(`wechat_django.pay.models.UnifiedOrderResult.State`) |
| attach | 结果附带的信息(生成订单时传给微信服务器的attach) |

使用示例

    from django.dispatch import receiver
    from wechat_django.pay import signals
    
    @receiver(signals.order_updated)
    def order_updated(result, order, state, attach):
        if state == UnifiedOrderResult.State.SUCCESS:
            pass

> 注意! 每次主动调用,微信通知或是后台重新触发都会发送信号,请自行确保订单成功信号逻辑只执行一次!

### django-rest-framework


## 后台使用简介
参见[管理后台使用简介](docs/admin.md) 文档

## 示例项目
可参考[本项目sample文件夹](sample)

## TODOS:
* 微信通知信号
* 改造patch_request为middleware,手工调用
* 改造handler为APIView
* 是否可做成migrate权限全自助?重构权限模块?
* 可选加密存储敏感数据
* [Cookbook](docs/cookbook/readme.md)
* app层面的message log和reply log
* 完善单元测试
* 后台表单验证

### 计划的功能
* 公众号迁移
* accesstoken开放给第三方并对接第三方accesstoken
* 客服消息/对话
* 清理及保护永久素材
* 回复及一些查询缓存
* 菜单及消息处理程序的导入导出
* 素材Storage

### 已知bugs
* 多次同步消息处理器会重复生成永久素材

## [Changelog](CHANGELOG.md)


Xavier-Lam@NetDragon