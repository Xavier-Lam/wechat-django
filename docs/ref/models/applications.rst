======================================
微信应用
======================================

.. module:: wechat_django.models.apps


Application
----------------

.. autoclass:: Application
   :members: title, name, desc, type, appid, appsecret, parent, pays, configuartions, storage, created_at, updated_at, session, get_class_by_type, logger

OrdinaryApplication
-----------------------

.. autoclass:: OrdinaryApplication
   :members: base_client, client, access_token


MiniprogramApplication
-------------------------

.. autoclass:: MiniProgramApplication
   :members: auth, decrypt_data, validate_data
             base_client, client, access_token,
             jsapi_ticket, jsapi_card_ticket,
             crypto, notify_url, decrypt_message, encrypt_message,
             parse_message, send_message


OfficialAccountApplication
-----------------------------

.. autoclass:: OfficialAccountApplication
   :members: base_client, client, access_token,
             jsapi_ticket, jsapi_card_ticket,
             crypto, notify_url, decrypt_message, encrypt_message,
             parse_message, send_message


WebApplication
-----------------

.. autoclass:: WebApplication
   :members: authorize_url, build_oauth_url, oauth, auth


微信支付应用
-----------------

.. autoclass:: PayApplication
   :members:


微信支付服务商应用
-----------------

.. autoclass:: PayMerchant
   :members:


微信支付子商户应用
-----------------

.. autoclass:: HostedPayApplication
   :members:


微信开放平台第三方平台
---------------------

.. autoclass:: ThirdPartyPlatform
   :members:


第三方平台托管小程序
--------------------

.. autoclass:: MiniProgramAuthorizerApplication
   :members:


第三方平台托管公众号
--------------------

.. autoclass:: OfficialAccountAuthorizerApplication
   :members: