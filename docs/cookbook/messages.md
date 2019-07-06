# 被动消息

- [被动消息](#被动消息)
  - [首次订阅](#首次订阅)
- [模板消息](#模板消息)
  - [发送模板消息](#发送模板消息)

## 被动消息
### 首次订阅
在开始使用本项目前,请先在后台或shell中同步关注app的所有用户.当接收到消息时,判断`message.local_user.subscribe`为非真值,在取用`message.user`将同步了所有信息的用户写库,如果未认证,可以手动将`message.local_user.subscribe`置为`True`,并且保存.

    import time
    from wechat_django import message_handler

    @message_handler
    def on_subscribe(message):
        user = message.local_user
        if not user.subscribe:
            # 首次订阅
            if message.app.authed:
                user = message.user
            else:
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