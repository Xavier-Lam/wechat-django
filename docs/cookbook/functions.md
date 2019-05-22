# 功能

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