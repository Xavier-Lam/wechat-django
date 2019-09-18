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

> 自定义处理规则应该是轻量并且无副作用的,抛出异常或不存在的自定义处理规则将被当作不匹配略过

### 首次订阅
从v0.3.3起,在监听订阅消息时,WeChat-Django会为用户附上first_subscribe属性,其中,首次订阅的用户,该值为真,否则为假
> 注意,需要使用本功能,请先同步公众号所有关注用户,否则,公众号在被WeChat-Django托管以后,第一次触发关注事件时,会被认为是首次关注

    @message_handler
    def on_subscribe(message):
        user = message.local_user
        if user.first_subscribe:
            # 首次关注
            pass

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