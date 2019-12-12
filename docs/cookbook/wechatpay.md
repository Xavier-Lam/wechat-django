# 微信支付

- [统一下单](#%e7%bb%9f%e4%b8%80%e4%b8%8b%e5%8d%95)
- [订单更新(回调)通知](#%e8%ae%a2%e5%8d%95%e6%9b%b4%e6%96%b0%e5%9b%9e%e8%b0%83%e9%80%9a%e7%9f%a5)

## 统一下单

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

## 订单更新(回调)通知

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