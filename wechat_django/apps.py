# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from . import settings


class WeChatConfig(AppConfig):
    name = "wechat_django"
    verbose_name = _("WeChat")
    verbose_name_plural = _("WeChat")

    def ready(self):
        from . import handler, views # NOQA
        if settings.PATCHADMINSITE:
            from .sites.admin import patch_admin
            patch_admin()
