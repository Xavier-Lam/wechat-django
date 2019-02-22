# 管理后台使用简介

[TOC]

## 首页
![首页预览](static/images/index.jpg?raw=true)

首页分为两个模块,一个是微信,是对微信号进行增删改查时使用,另一个模块微信号则提供你拥有权限管理的微信号的内容管理.

## 微信号管理
### 新增微信号
![新增微信号](static/images/add_wechatapp.jpg?raw=true)

在新增微信号页面中,你需要填写微信号的
* 标题(建议填写微信号名称,用于后台人工辨识微信号)
* 名称(建议填写微信号,全局唯一,用于程序辨识,创建后不可修改)
* AppId 创建后不可修改
* 选择微信号类型
创建成功后,进入编辑页面会出现消息回调地址,将该地址填写至公众平台的开发者配置中并启用
![微信配置](static/images/wechat_config.jpg?raw=true)

### 内容管理
![内容管理](static/images/wechat_content_manage.jpg?raw=true)

在首页的微信号中,会出现我们刚刚新增的测试订阅号,点击进入,会出现内容管理菜单
> 注意!如非超管配置的新公众号,需要手动给该管理员配置新公众号的权限,方可在首页上出现新配置的公众号

### 用户管理
![用户管理](static/images/user_manage.jpg?raw=true)

可通过动作更新关注公众号的用户
> 注意!未认证的微信号没有同步用户权限

### 自动回复管理
![自动回复管理](static/images/message_handlers.jpg?raw=true)

可通过调整权重来调整规则匹配的顺序(权重越大,则越靠前,否则越靠后,权重可为负数)

#### 同步自动回复
在自动回复列表中,可通过同步动作,来同步在微信后台配置的所有自动回复
> 注意!每次重新同步,将移除之前从微信后台同步且**未经编辑**的自动回复

#### 编辑自动回复
![编辑自动回复](static/images/handler_edit.jpg?raw=true)

自动回复可设置是否开启,是否记录日志,以及回复的策略

##### 规则
![规则](static/images/rule_edit.jpg?raw=true)

一个自动回复可包含一个或多个规则,当消息匹配任一规则时,将按照回复策略,执行下面的回复
> 注意!匹配规则后,将不再对剩余的规则或是自动回复进行匹配

##### 回复
![规则](static/images/reply_edit.jpg?raw=true)

一个自动回复可包含一个或多个回复,当回复策略为全部回复时,将依次执行所有回复,对于随机回复,将随机回复以下任一回复内容
> 注意!对于未认证的微信号,全部回复会依次执行所有回复的处理逻辑,但只会成功回复最后一则回复

### 菜单管理
![菜单管理](static/images/menu_manage.jpg?raw=true)

可通过菜单管理同步或发布菜单

### 素材及图文
![素材管理](static/images/material_manage.jpg?raw=true)

可通过素材后台同步和远程删除永久素材

### 权限
![权限列表](static/images/permissions.jpg?raw=true)

可给管理员分配微信管理权限,所有微信权限以 `<appname> | <perm>` 标注.其中Can full control %(appname)s 代表拥有 %(appname)s 的所有权限, Can manage %(appname)s 代表仅拥有编辑 %(appname)s 公众号设置的权限,其他权限为各功能自有权限.

> 注意!在赋予用户权限时,系统会自动为用户追加所需的django默认权限,请勿删除!注意,请不要自行分配wechat_django的默认model权限给用户,这是毫无作用的