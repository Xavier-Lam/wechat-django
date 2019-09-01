# 被动消息

- [被动消息](#%e8%a2%ab%e5%8a%a8%e6%b6%88%e6%81%af)
  - [自定义处理规则](#%e8%87%aa%e5%ae%9a%e4%b9%89%e5%a4%84%e7%90%86%e8%a7%84%e5%88%99)
  - [首次订阅](#%e9%a6%96%e6%ac%a1%e8%ae%a2%e9%98%85)
- [模板消息](#%e6%a8%a1%e6%9d%bf%e6%b6%88%e6%81%af)
  - [发送模板消息](#%e5%8f%91%e9%80%81%e6%a8%a1%e6%9d%bf%e6%b6%88%e6%81%af)

## 被动消息
### 自定义处理规则
在后台配置自定义规则,填写自定义回复处理代码的路径,代码须由 `wechat_django.handler.message_rule` 装饰对应的方法接收一个 `wechat_django.models.WeChatMessageInfo` 对象,返回一个bool值,真值代表规则匹配

    from wechat_django import message_rule

    @message_rule
    def custom_business(message):
        """
        :type message: wechat_django.models.WeChatMessageInfo
        """
        user = message.user
        return user.openid == "1234567"

### 首次订阅
在开始使用本项目前,请先在后台或shell中同步关注app的所有用户.当接收到消息时,判断`message.local_user.subscribe`为非真值,再通过`message.user.update()`同步用户信息并写库,如果未认证,可以手动将`message.local_user.subscribe`置为`True`,并且保存.

    import time
    from wechat_django import message_handler

    @message_handler
    def on_subscribe(message):
        user = message.local_user
        if not user.subscribe:
            if message.app.authed:
                # 认证公众号 直接拉取用户信息
                user.update()
            else:
                # 未认证公众号 手动更新信息
                user.subscribe = True
                user.subscribe_time = time.time()
                user.save()

## 模板消息
### 发送模板消息
在后台完成模板同步后,可通过

    from wechat_django.models import WeChatApp
    app = WeChatApp.objects.get_by_name("app")
    user = app.users.first()
    template = app.templates.get(name="在后台设置的模板名")
    template.send(
        user, # 亦可以用openid代替WeChatUser对象
        url="https://baidu.com",
        # 此后为模板上的keyword
        keyword1="keyword1",
        keyword2="keyword2",
        remark="remark"
    )

对于小程序模板消息,也是使用相同的api发送,但必须填写form_id

    template.send(
        user,
        form_id=form_id,
        pagepath="/index",
        # 此后为模板上的keyword
        keyword1="keyword1",
        keyword2="keyword2"
    )