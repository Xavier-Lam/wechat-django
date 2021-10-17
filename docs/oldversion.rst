==========================
The Former Version
==========================


The new WeChat-Django is complete different to the elder one, it is
easier to use and contribute to, more extendable, more pythonic, and more
Django like.

I intended to restruct the elder one but failed, so I decided to rewrite it.
You can look up the following instruction to decide whether you should use the
newer one.



The mainly differences between the two versions
------------------------------------------------

The new version only developed the basic functions with limited
administrations, the following administrations have not been included and
you have to develop by yourself for now.

* `Media assets management <https://developers.weixin.qq.com/doc/offiaccount/Asset_Management/New_temporary_materials.html>`_
* `Custom menus <https://developers.weixin.qq.com/doc/offiaccount/Custom_Menus/Creating_Custom-Defined_Menu.html>`_
* `WeChat messages <https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Receiving_standard_messages.html>`_
* `Template messages <https://developers.weixin.qq.com/doc/offiaccount/Message_Management/Template_Message_Interface.html>`_


.. note::

    Do not be panic, I think it is easy to write your own, I am strongly
    recommend you to use the newer one. Once you wrote your admin, you can
    choose to contribute to our project!


.. note::

    Although I recommend using the newer one, I have to say I have not used
    this project in production environment for now, but the elder one does.


And the newer one provided an important function which old one did not have,
it is `the third party platform
<https://developers.weixin.qq.com/doc/oplatform/Third-party_Platforms/2.0/product/Third_party_platform_appid.html>`_.
It is easy to use, you do not need to do anything besides set up your platform
on your admin, and this function is fully unit tested.


Install the old version
------------------------------

You can install the old version by using pip.

    > pip install wechat-django<2.0.0


And you will find the basic tuturial here.


.. warning::

    The repository also has a `0.4.0` branch, which is a deprecated
    development branch, please use `0.3.3` instead, it is the latest
    stable version.