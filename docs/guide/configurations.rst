=================
Configurations
=================


Core configuartions
------------------------

WECHAT_DJANGO_SECRET_KEY
+++++++++++++++++++++++++++

* Default: `django.conf.settings.SECRET_KEY`

The key for secret keys (such as `AppSecret`, `API_KEY`) encrypting when
persisted, if you don't want to encrypt your keys, set the value to `None`
explicitly.


.. warning::

    Once the key has been changed, **all your secret keys stored in your 
    database will become invalid**. Make sure you have migrated your keys
    well when you change this setting.



Function enabling
-------------------------
You can toggle these settings to enable/disable some functions in WeChat
-Django

========================================  ==============  ========================================
**Setting name**                          **Default**     **Function**
========================================  ==============  ========================================
WECHAT_DJANGO_ENABLE_MERCHANT             True            WeChat Pay merchant
WECHAT_DJANGO_ENABLE_THIRDPARTYPLATFORM   True            WeChat third party platform
WECHAT_DJANGO_ENABLE_WECHATPAY            True            WeChat Pay
========================================  ==============  ========================================


General settings
------------------------

.. _WECHAT-DJANGO-OAUTH-LOGIN-HANDLER:

``WECHAT_DJANGO_OAUTH_LOGIN_HANDLER``
++++++++++++++++++++++++++++++++++++++++++

* Default: ``"wechat_django.oauth.oauth_login"``

The default WeChat webpage authorization login handler for
:class:`wechat_django.views.oauth.OAuthProxyView`.
