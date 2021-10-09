=======
信号
=======

WeChat-Django 内置了一些基础信号,所有信号均在 :mod:`~wechat_django.signals` 中定义.信号的 `sender` 均为 :class:`~wechat_django.models.Application` 的 `name`

例如,你可以通过这样的方式监听一个信号::

    from django.dispatcher import receiver
    from wechat_django import signals

    @receiver(signals.message_received, sender="appname")
    def message_received(wechat_app, message, request):
        pass


消息处理相关信号
=================

``message_received``
--------------------------

.. data:: wechat_django.signals.message_received
   :module:

消息处理器接收到消息

``wechat_app``
    接收到消息的 :class:`~wechat_django.models.Application` 实例

``message``
    接收到的消息 :class:`~wechatpy.messages.BaseMessage` 或 :class:`~wechatpy.component.BaseComponentMessage` 实例

``request``
    当前请求 :class:`~django.http.HttpRequest` 实例


``message_replied``
--------------------------

.. data:: wechat_django.signals.message_replied
   :module:

消息处理器成功响应消息

``wechat_app``
    接收到消息的 :class:`~wechat_django.models.Application` 实例

``reply``
    发送的响应 :class:`~wechatpy.replies.BaseReply` 实例

``message``
    接收到的消息 :class:`~wechatpy.messages.BaseMessage` 或 :class:`~wechatpy.component.BaseComponentMessage` 实例

``response_content``
    响应的原始content


``message_handle_failed``
--------------------------

.. data:: wechat_django.signals.message_handle_failed
   :module:

消息处理器处理消息过程中抛出异常(不包含验证请求及转化消息时发生的异常)

``wechat_app``
    接收到消息的 :class:`~wechat_django.models.Application` 实例

``message``
    接收到的消息 :class:`~wechatpy.messages.BaseMessage` 或 :class:`~wechatpy.component.BaseComponentMessage` 实例

``exc``
    发生的异常

``request``
    当前请求 :class:`~django.http.HttpRequest` 实例


``message_sent``
--------------------------

.. data:: wechat_django.signals.message_sent
   :module:

主动推送消息成功

``wechat_app``
    接收到消息的 :class:`~wechat_django.models.Application` 实例

``reply``
    推送的消息 :class:`~wechatpy.replies.BaseReply` 实例

``message``
    接收到的消息 :class:`~wechatpy.messages.BaseMessage` 或 :class:`~wechatpy.component.BaseComponentMessage` 实例


``message_send_failed``
--------------------------

.. data:: wechat_django.signals.message_send_failed
   :module:

主动推送消息时发生的异常

``wechat_app``
    接收到消息的 :class:`~wechat_django.models.Application` 实例

``reply``
    推送的消息 :class:`~wechatpy.replies.BaseReply` 实例

``message``
    接收到的消息 :class:`~wechatpy.messages.BaseMessage` 或 :class:`~wechatpy.component.BaseComponentMessage` 实例

``exc``
    发生的异常

``request``
    当前请求 :class:`~django.http.HttpRequest` 实例