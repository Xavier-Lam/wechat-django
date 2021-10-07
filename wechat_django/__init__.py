# flake8: noqa

__title__ = "wechat-django"
__description__ = "Django WeChat Extension"
__url__ = "https://github.com/Xavier-Lam/wechat-django"
__version__ = "2.0.0-alpha"
__author__ = "Xavier-Lam"
__author_email__ = "xavierlam7@hotmail.com"

default_app_config = "wechat_django.apps.WeChatDjangoConfig"


from .sites import default_site as site
