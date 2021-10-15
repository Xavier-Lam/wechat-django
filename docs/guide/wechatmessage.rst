========================
WeChat Messages
========================

You can setup your message listeners by decorating a handler function with
:func:`wechat_django.message_handlers`.


.. decorator:: wechat_django.message_handlers

.. automethod:: wechat_django.messagehandler.base.MessageHandlerCollection.register


The decorated handler should look like this:

.. automethod:: wechat_django.messagehandler.base.MessageResponder.handler
