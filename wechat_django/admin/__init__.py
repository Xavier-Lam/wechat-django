# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.module_loading import import_string

from .. import settings
from . import ( # NOQA
    base,
    wechatapp,
    user,
    usertag,
    menu,
    messagehandler,
    messagelog,
    material,
    article
)

admin_site_paths = settings.ADMINSITE
if not isinstance(admin_site_paths, (list, tuple)):
    admin_site_paths = [admin_site_paths]
for site in admin_site_paths:
    admin = import_string(site)
    base.patch_admin(admin)
    base.register_admins(admin)
