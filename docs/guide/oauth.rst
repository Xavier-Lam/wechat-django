==============================
WeChat Webpage Authorization
==============================

.. note::

        Before you read the documentation, make sure you already got the basic
        knowledge of WeChat webpage authorization. If not, you should read
        `the official documentation <https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/Wechat_webpage_authorization.html>`_
        first.


.. module:: wechat_django.oauth


When you are developing a web app using WeChat webpage authorization, your
views should inherit from :class:`~.WeChatOAuthView`, and you should assign
your `WeChat app name` to the :attr:`~.WeChatOAuthViewMixin.wechat_app_name`
attribute.

You can access the logined :class:`~wechat_django.models.User`
instance by using `request.user` and access the current
:class:`~wechat_django.models.apps.Application` instance by using
`request.wechat_app`.



Default authentication flow
------------------------------

By using :class:`~.WeChatOAuthView` without any other configuartions, the
request will do the following things.

When a request reached your view, we will validate if the coming request has
been granted by user. If not, we will ask user to grant required scopes by
redirecting to the WeChat's authentication page. 

After user has granted permissions, the request will turn to our proxy page,
in which we exchange the authorized code to openid and access token, and set
the openid to django's builtin :doc:`session <django:topics/http/sessions>`.

Finally, we will return to the origin page user visited, now the request is
authorized, you can access current user now.



Non-class-based view
----------------------------------

When you are writing a non-class-based view, you can use :func:`~wechat_oauth`
to decorate your view.

.. autodecorator:: wechat_oauth


Setup your own authenticator
----------------------------------

In most cases, you will have your own user model in your business instead use
our :class:`~wechat_django.models.User` class directly. You need to write and
use your own
`Authenticator <https://www.django-rest-framework.org/api-guide/authentication/>`_.

Your `Authenticator` should inherit from
:class:`~wechat_django.authentication.OAuthSessionAuthentication`, and
override the
:func:`~wechat_django.authentication.OAuthSessionAuthentication.authenticate`
method.

In the override, you need to call the parent authenticate first to get the
wechat_user instance, then using the instance to get your user instance.

.. code-block:: python

        from wechat_django.authentication import OAuthSessionAuthentication


        class BusinessAuthentication(OAuthSessionAuthentication):
            def authenticate(self, request):
                auth = super().authenticate(self, request)
                if not auth:
                    return
                wechat_user, openid = auth
                
                # get your user instance
                user = BussinessUser.objects.get(wechat_user=wechat_user)

                return user, your_token



In your view declaration, replace the
:attr:`~wechat_django.oauth.WeChatOAuthView.authentication_classes` attribute
with the authenticator you have written.

.. code-block:: python

        from wechat_django import WeChatOAuthView


        class BussinessView(WeChatOAuthView):
            authentication_classes = (BusinessAuthentication,)



Change unauthorization response
-----------------------------------

By default, WeChat-Django automaticly response a `302 Found` to client, which
will eventually return to current page. But when the request comes from an
ajax request, it will not work properly. In this case, you should override the
:func:`~wechat_django.oauth.WeChatOAuthViewMixin.unauthorized_response` method
to customise the response sends to client.

.. code-block:: python

    from django.http import JsonResponse
    from wechat_django import WeChatOAuthView


    class YourView(WeChatOAuthView):
        def unauthorized_response(self, url, request):
            return JsonResponse({"code": 401, "data": {"url": url}})



Replace the default session
----------------------------------

We use django's session to store user credentials. Sometimes, you may need an
alternative option to replace the default session, such as when you interact
with your client by using a token on request header instead of cookies.

Write your own oauth login handler by replicate :func:`oauth_login`, and
change the :ref:`WECHAT-DJANGO-OAUTH-LOGIN-HANDLER` setting to your login
handler.

I recommend using the `state` param to decide how you login user and what
response you would like to send to your client.