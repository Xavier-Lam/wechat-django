# 小程序

- [小程序授权](#%e5%b0%8f%e7%a8%8b%e5%ba%8f%e6%8e%88%e6%9d%83)
- [小程序信息加解密](#%e5%b0%8f%e7%a8%8b%e5%ba%8f%e4%bf%a1%e6%81%af%e5%8a%a0%e8%a7%a3%e5%af%86)
- [用户数据更新](#%e7%94%a8%e6%88%b7%e6%95%b0%e6%8d%ae%e6%9b%b4%e6%96%b0)

## 小程序授权
通过`wechat_django.models.WeChatApp.auth`进行授权,输入客户端传来的code, 输出一个用户对象以及原始响应.这个方法只能拿到用户的openid与unionid.

    from wechat_django.models import WeChatApp
    app = WeChatApp.objects.get_by_name("your app name")
    user, data = app.auth(code)

对于授权后得到的session_key,框架会持久化至数据库,此后可以通过调用`wechat_django.models.MiniProgramUser.session`来执行相关操作.

auth方法同样适用于网页授权,第二个参数填写网页授权的scope,默认base.

## 小程序信息加解密
对于已经进行过小程序授权并且session_key尚未过期的用户,可以使用`wechat_django.models.MiniProgramUser.session.decrypt_message`来解密客户端传来的敏感数据

    encrypted_data = ""
    iv = ""
    try:
        data = user.session.decrypt_message(encrypted_data, iv)
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

## 用户数据更新
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