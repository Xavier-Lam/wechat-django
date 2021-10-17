=============================
Quickstart
=============================


Setup your applications on admin
-----------------------------------------



Get your applications
-----------------------------------------

According to the type of your :class:`~wechat_django.models.apps.Application`,
the queryset will return different kinds of instances. For more information,
please look up the :doc:`reference <ref/models/applications>`.

.. code:: python

    from wechat_django.models import Application


    app = Application.objects.get(name="yourminiprogram")  # type: MiniProgramApplication
    app = Application.objects.get(name="yourofficialaccount")  # type: OfficialAccountApplication


In a view inherit from :class:`~wechat_django.core.view.WeChatViewMixin`,
you can get your application by accessing `request.wechat_app` property.


.. code:: python

    def get(self, request, *args, **kwargs):
        app = request.wechat_app



Deal with WeChat messages
-------------------------------------------

You can use the :func:`~wechat_django.message_handlers` decorator to
decorate a handler to process messages sent by WeChat server.


.. code-block:: python

    from wechat_django import message_handlers


    @message_handlers(app_names="your app name", query={"type": "text"})
    def handler(message, request, *args, **kwargs):
        app = request.wechat_app
        user = request.user


In most of time, the first param pass to your handler is a
:class:`wechatpy.messages.BaseMessage` instance, except for some situations
like a third party platform ticket update. The second param is
django's :class:`~django.http.HttpRequest`, similar to other situations,
there is a `wechat_app` property to get your
:class:`~wechat_django.models.apps.Application` instance. When the message
contains a `source` attribute, you can get the
:class:`~wechat_django.models.User` instance by using `request.user`.

For more instructions, please read :doc:`the guide <guide/wechatmessage>`.



Develop a WeChat web application
--------------------------------------------

When you want to develop a WeChat web application, our project can help you a
lot, just inherit your view from :class:`~wechat_django.oauth.WeChatOAuthView`
and write your bussiness like this:


.. code-block:: python

    from wechat_django import WeChatOAuthView


    class BussinessView(WeChatOAuthView):
        wechat_app_name = "your app name"

        def get(self, request, *args, **kwargs):
            app = request.wechat_app
            user = request.user


You can achieve the :class:`~wechat_django.models.apps.Application` instance
by the `wechat_app` property of request, and :class:`~wechat_django.models.User`
by the `user` property.

Alternatively, you can use :func:`~wechat_django.oauth.wechat_oauth` to
decorate a function based view.


.. code-block:: python

    from wechat_django import wechat_oauth


    @wechat_oauth("your app name")
    def view(request, *args, **kwargs):
        app = request.wechat_app
        user = request.user


Read :doc:`the guide <guide/oauth>` for more details.



Request WeChat APIs
--------------------------



Using WeChat JSAPIs
-------------------------------



Host a third party platform
-------------------------------