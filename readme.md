# wechat_django

本拓展基于[wechatpy](https://github.com/jxtech/wechatpy) ,旨在为有在django框架下接入微信公众平台的开发者提供便利.支持的最低django版本为1.11.

[TOC]

## 功能
* 最基本的公众号管理
* 最基本的用户管理
* 最基本的菜单管理
* 最基本的自动回复管理
* 最基本的素材管理
* 服务号网页授权
* 主动调用微信api封装

## 安装

1. 安装
    
    pip install wechat_django

2. 在settings.py的**INSTALLED_APPS中添加wechat_django**
3. 运行manage.py migrate 来更新数据库结构
4. 在urls.py 中引入wechat_django.urls.urls, 将其配置到urlpatterns中

至此,您已可以开始轻松使用wechat_django.项目尚未提供具体的使用文档,如需客制化需求,烦请先阅读代码

## 配置
| 参数名 | 默认值 | 说明 |
| --- | --- | --- |
| ADMINSITE | "django.contrib.admin.site" | 需要注册微信后台的AdminSite对象字符串 |

## 部分功能使用说明
### 网页授权

### 主动调用微信api
    from wechat_django.models import WeChatApp
    app = WeChatApp.get_by_name("your app name")
    data = app.client.user.get_followers()

具体client的使用方式,请移步[wechatpy文档](https://wechatpy.readthedocs.io/zh_CN/master/client/index.html)

## 预览

## TODOS:
* 完整的素材管理
* 完整的图文管理
* 完整的用户管理
* 权限管理
* 文档
* 单元测试