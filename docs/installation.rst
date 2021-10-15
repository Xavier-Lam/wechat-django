====================================
Install and Setup Your Project
====================================


Install first time
------------------------


1. Install WeChat-Django via pip

   .. code-block:: bash

        $ pip install wechat-django


2. Add **wechat_django** to your **INSTALLED_APPS** and set **USE_TZ = True**
   in your project setting file.

   .. code-block:: python

        # settings.py

        INSTALLED_APPS = [
            ...
            'wechat_django',
        ]

        USE_TZ = True


3. Register **wechat_django.site.urls** to your **urlpatterns**

   .. code-block:: python

        # urls.py

        from django.contrib import admin
        from django.conf.urls import url

        import wechat_django


        urlpatterns = [
            url(r'^admin/', admin.site.urls),
            url(r'^wechat/', wechat_django.site.urls),
        ]


4. Migrate your database

   .. code-block:: bash

        $ python manage.py migrate wechat_django



.. note::

    You may meet problems when install WeChat-Django on windows. The
    `cryptography` dependency need to be compiled when installing, which lead
    to a problem if you have not properbly setuped your compile tools.

    You can `download the pre compiled whl file from pypi
    <https://pypi.org/project/cryptography/#files>`_, and install it manually.



Update
------------------------


1. Upgrade WeChat-Django

   .. code-block:: bash

        $ pip install -U wechat-django


2. Migrate your database

   .. code-block:: bash

        $ python manage.py migrate wechat_django



Install to your project
---------------------------

Sometimes you may want to use the latest features that has not been published,
or you want to customize WeChat-Django, you can install WeChat-Django to your
project's root folder.


   .. code-block:: bash

        $ cd <your project home directory>
        $ pip install -e git+https://github.com/Xavier-Lam/wechat-django.git -t .