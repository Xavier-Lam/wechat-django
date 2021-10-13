# WeChat-Django

[![PyPI](https://img.shields.io/pypi/v/wechat-django.svg)](https://pypi.org/project/wechat-django)
[![Build Status](https://travis-ci.org/Xavier-Lam/wechat-django.svg?branch=master)](https://travis-ci.org/Xavier-Lam/wechat-django)
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)](https://en.cryptobadges.io/donate/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)

项目官方地址: https://github.com/Xavier-Lam/wechat-django

本拓展基于[wechatpy](https://github.com/jxtech/wechatpy) ,支持的最低django版本为2.2.

- [安装](#安装)
  - [初次安装](#初次安装)
  - [直接加入项目](#直接加入项目)
  - [更新](#更新)
- [配置](#配置)
  - [核心配置](#核心配置)
  - [功能启用](#功能启用)
  - [其他配置项](#其他配置项)
- [快速上手](#快速上手)
  - [获取应用实例](#获取应用实例)
  - [主动调用微信接口](#主动调用微信接口)
  - [使用微信jssdk](#使用微信jssdk)
    - [静态页面](#静态页面)
    - [模板页](#模板页)
- [使用指引](#使用指引)
  - [消息推送与处理](#消息推送与处理)


## 安装
### 初次安装

1. 运行 **pip install wechat-django** 安装
2. 在项目配置文件的 **INSTALLED_APPS** 中添加 **wechat_django**, 并设置 **USE_TZ = True**
3. 在项目路由文件 **urlpatterns** 中配置 **wechat_django.site.urls**
4. 运行 **manage.py migrate wechat_django** 来更新数据库结构

### 直接加入项目
想使用最新特性或是自行编辑代码,可clone本项目后,采用 **pip install -e** 直接安装到你的django项目目录

### 更新

1. 运行 **pip install -U wechat-django**
2. 运行 **python manage.py migrate** 来更新数据库结构


## 配置
### 核心配置
| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| WECHAT_DJANGO_SECRET_KEY | django.conf.settings.SECRET_KEY | 加密微信各密钥(如AppSecret,API_Key等)用密钥,如无需加密,请置为`None`.**注意,该密钥一旦修改,所有已存储密钥将失效**,修改密钥请自行做好密钥迁移工作 |

### 功能启用
| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| WECHAT_DJANGO_ENABLE_MERCHANT | True | 是否开启微信支付服务商功能 |
| WECHAT_DJANGO_ENABLE_THIRDPARTYPLATFORM | True | 是否开启第三方平台功能 |
| WECHAT_DJANGO_ENABLE_WECHATPAY | True | 是否开启微信支付功能 |

### 其他配置项
| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| WECHAT_DJANGO_OAUTH_LOGIN_HANDLER | "wechat_django.oauth.oauth_login" | 微信网页授权默认登录处理器 |


## 快速上手
### 获取应用实例
在代码中可以通过 `Application` 类主动获取应用实例

    from wechat_django.models import Application
    app = Application.objects.get(name="appname")

在继承 `wechat_django.views.WeChatView` 或以 `wechat_django.views.wechat_view` 的视图中,可以采用 `request.wechat_app` 来获取当前请求的应用实例

### 主动调用微信接口
通过 `app.client` 获取到 `wechatpy` 的client实例],对于不同类型app,实例类型不同.

| App类型 | Client类型 |
| --- | --- |
| OrdinaryApplication/OfficialAccountApplication | [wechatpy.WeChatClient](https://wechatpy.readthedocs.io/zh_CN/master/client/index.html) |
| ThirdPartyPlatform | [wechatpy.WeChatComponent](https://wechatpy.readthedocs.io/zh_CN/master/component.html) |
| OfficialAccountAuthorizerApplication | [wechatpy.client.WeChatComponentClient](https://wechatpy.readthedocs.io/zh_CN/master/client/index.htm) |
| MiniProgramApplication/MiniProgramAuthorizerApplication | [wechatpy.client.api.WeChatWxa](https://wechatpy.readthedocs.io/zh_CN/master/client/wxa.html) |

### 使用微信jssdk
#### 静态页面
    <script src="//res.wx.qq.com/open/js/jweixin-1.6.0.js"></script>
    <script src="/{URLPATTERN}/{YOURAPPNAME}/jssdk.config.js"></script>

#### 模板页
    <script src="//res.wx.qq.com/open/js/jweixin-1.6.0.js"></script>
    <script src="{% url 'wechat_django:jsconfig' app_name=wechat_app.name %}"></script>


## 使用指引
### 消息推送与处理
> 在单元测试过程中,我们发现使用message_handlers时复合使用以下几个参数时存在较大风险
> * `pass_through`为`True`且`ignore_errors`为`False`: 此时你可能期望完整执行所有处理器,但是由于前序处理器抛出了异常,后续处理器将无法继续执行,前序处理器业务逻辑已完成执行,用户无法收到任何响应
> * `match_all`为`True`,match_all参数为真时将捕获所有通过的请求,因为第三方平台通知与一般通知响应差异较大,如处理器内处理不当,容易抛出异常,可能与你的业务逻辑设计初衷违背.
> * `match_all`为`True`且`pass_through`为`False`并且处理器有较高`weight`或较早注册:处理器会拦截消息,处理并响应,造成后续处理器失效