=======
Signals
=======


.. module:: wechat_django.signals


There are many builtin signals in WeChat-Django, all of them are defined in
:mod:`~wechat_django.signals`. The `sender` of the signals is the name of the
:class:`~wechat_django.models.apps.Application`.

For example, you can listen to a signal by following code

.. code-block:: python

    from django.dispatcher import receiver
    from wechat_django import signals

    @receiver(signals.message_received, sender="appname")
    def message_received(wechat_app, message, request):
        pass


Message handler signals
========================

``message_received``
--------------------------

.. autodata:: wechat_django.signals.message_received
   :annotation:


``message_replied``
--------------------------

.. autodata:: wechat_django.signals.message_replied
   :annotation:


``message_handle_failed``
--------------------------

.. autodata:: wechat_django.signals.message_handle_failed
   :annotation:


``message_sent``
--------------------------


.. autodata:: wechat_django.signals.message_sent
   :annotation:


``message_send_failed``
--------------------------


.. autodata:: wechat_django.signals.message_send_failed
   :annotation:


Webpage authorization signals
======================================


``post_oauth``
--------------------------


.. autodata:: wechat_django.signals.post_oauth
   :annotation: