# WeChat-Django

[![PyPI](https://img.shields.io/pypi/v/wechat-django.svg)](https://pypi.org/project/wechat-django)
[![Build Status](https://travis-ci.org/Xavier-Lam/wechat-django.svg?branch=master)](https://travis-ci.org/Xavier-Lam/wechat-django)
[![Donate with Bitcoin](https://en.cryptobadges.io/badge/micro/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)](https://en.cryptobadges.io/donate/1BdJG31zinrMFWxRt2utGBU2jdpv8xSgju)

**WeChat-Django**旨在为使用django开发微信公众号,小程序,支付等功能的开发者提供便捷的功能封装及基本的[**后台管理支持**](docs/admin.md).

项目官方地址: https://github.com/Xavier-Lam/wechat-django

本拓展基于[wechatpy](https://github.com/jxtech/wechatpy) ,支持的最低django及python版本可参考[tox.ini](tox.ini). WeChat-Django只是一个预览版本,可能存在较多bug并且有api及数据结构变更可能,请密切关注[CHANGELOG](CHANGELOG.md).

目录
======
- [功能](#%e5%8a%9f%e8%83%bd)
  - [公众号](#%e5%85%ac%e4%bc%97%e5%8f%b7)
  - [小程序](#%e5%b0%8f%e7%a8%8b%e5%ba%8f)
  - [微信支付](#%e5%be%ae%e4%bf%a1%e6%94%af%e4%bb%98)
  - [网页应用](#%e7%bd%91%e9%a1%b5%e5%ba%94%e7%94%a8)
  - [通用开发](#%e9%80%9a%e7%94%a8%e5%bc%80%e5%8f%91)
- [安装及配置](#%e5%ae%89%e8%a3%85%e5%8f%8a%e9%85%8d%e7%bd%ae)
  - [初次安装](#%e5%88%9d%e6%ac%a1%e5%ae%89%e8%a3%85)
    - [直接加入项目](#%e7%9b%b4%e6%8e%a5%e5%8a%a0%e5%85%a5%e9%a1%b9%e7%9b%ae)
  - [更新](#%e6%9b%b4%e6%96%b0)
  - [配置](#%e9%85%8d%e7%bd%ae)
  - [日志](#%e6%97%a5%e5%bf%97)
  - [注意事项](#%e6%b3%a8%e6%84%8f%e4%ba%8b%e9%a1%b9)
- [TODOS:](#todos)
  - [计划的功能](#%e8%ae%a1%e5%88%92%e7%9a%84%e5%8a%9f%e8%83%bd)
  - [已知bugs](#%e5%b7%b2%e7%9f%a5bugs)
- [Changelog](#changelog)


## 功能
### 公众号
* 公众号管理
* 用户及用户标签的同步及管理
* [自动回复的同步,管理,转发,自定义自动回复业务,接收消息的日志](docs/cookbook/messages.md#被动消息)
* 公众号菜单的同步,管理及发布
* 永久素材,图文的同步及查看
* 模板消息模板的同步及[发送](docs/cookbook/messages.md#发送模板消息)
* [微信网页授权](docs/cookbook/web.md#服务号网页授权)
* [微信jsapi配置](docs/cookbook/web.md#jsapi)
* [主动调用微信api封装](docs/cookbook/api.md)
* [django-rest-framework APIView兼容](docs/cookbook/advance-dev.md#django-rest-framework)
* 迁移公众号自动回复/菜单/素材(不建议迁移素材)

### [小程序](docs/cookbook/miniprogram.md)
* 小程序管理
* 用户管理
* 模板消息模板的同步及发送
* [主动调用小程序api封装](docs/cookbook/api.md)

### 微信支付
需要使用微信支付相关功能,需要在`INSTALLED_APP`中的`wechat_django`之后额外加入`wechat_django.pay`.
* [统一下单](docs/cookbook/wechatpay.md#统一下单)
* 微信支付api封装
* 微信支付订单管理及[信号](docs/cookbook/wechatpay.md#订单更新(回调)通知)
* 服务商商户号的兼容(未有使用案例)

### [网页应用](docs/cookbook/web.md#开放平台网站应用)

### 通用开发
* [后台权限管理](docs/admin.md#权限)

## 安装及配置
### 初次安装
1. 运行**pip install wechat-django[cryptography]** 或 **pip install wechat-django[pycrypto]** 安装
2. 在settings.py的**INSTALLED_APPS中添加wechat_django**
3. 运行**manage.py migrate** 来更新数据库结构
4. 在urls.py 中引入wechat_django.sites.wechat.urls, 将其配置到urlpatterns中
5. 在settings.py中,设置`USE_TZ = True`

至此,您已可以开始轻松使用wechat_django.项目的使用和配置可参考[示例项目](sample)

#### 直接加入项目
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

## TODOS:
* 是否可做成migrate权限全自助?重构权限模块?
* 可选加密存储敏感数据
* [Cookbook](docs/cookbook/readme.md)
* app层面的message log和reply log
* 完善单元测试
* 后台功能优化

### 计划的功能
* 命令行工具
* 第三方平台接入
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