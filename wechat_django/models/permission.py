# -*- coding: utf-8 -*-

"""权限模块
约定:
对于manage,article 这种每个公众号拥有的权限,变量名用permission
对于{prefix}{appname}|{perm} 这种permission表中的codename,变量名用perm_name
对于可能携带applabel的codename,变量名亦用perm_name
对于Permission对象,变量名用perm
"""

from __future__ import unicode_literals

from collections import defaultdict
import re

from django.contrib.auth.models import Group, Permission, User
from django.db import models as m
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

WECHATPERM_PREFIX = "app|"

permissions = {
    "manage": _("Can manage %(appname)s"),
    "article": _("Can edit %(appname)s articles"),
    "article_sync": _("Can sync %(appname)s articles"),
    "material": _("Can edit %(appname)s materials"),
    "material_sync": _("Can sync %(appname)s materials"),
    "menu": _("Can edit %(appname)s menus"),
    "menu_sync": _("Can sync %(appname)s menus"),
    "menu_publish": _("Can publish %(appname)s menus"),
    "messagehandler": _("Can edit %(appname)s message handlers"),
    "messagehandler_sync": _("Can sync %(appname)s message handlers"),
    "messagelog": _("Can view %(appname)s message logs"),
    "user": _("Can edit %(appname)s users"),
    "user_sync": _("Can sync %(appname)s users"),
    "usertag": _("Can edit %(appname)s user tags"),
    "usertag_sync": _("Can sync %(appname)s user tags"),    
}

permission_required = {
    "material": (
        "article",
        "wechat_django.delete_material"
    ),
    "article": (
        "wechat_django.delete_article",
    ),
    "menu": (
        "wechat_django.delete_menu",
    ),
    "messagehandler": (
        "wechat_django.delete_messagehandler",
        "wechat_django.add_reply",
        "wechat_django.change_reply",
        "wechat_django.delete_reply",
        "wechat_django.add_rule",
        "wechat_django.change_rule",
        "wechat_django.delete_rule"
    )
}


def list_perm_names(app):
    """列举该app下的所有权限"""
    rv = set()
    rv.add(get_perm_name(app))
    rv.update(
        get_perm_name(app, permission)
        for permission in permissions
    )
    return rv


def get_perm_name(app, permission=""):
    if not permission:
        return "{prefix}{appname}".format(
            prefix=WECHATPERM_PREFIX,
            appname=app.name
        )
    return "{prefix}{appname}|{permission}".format(
        prefix=WECHATPERM_PREFIX,
        appname=app.name,
        permission=permission
    )


def get_perm_desc(perm_name, app):
    appname, permission = match_permission(perm_name)
    desc = permissions[permission] if permission\
        else _("Can full control %(appname)s")
    return "{0} | {1}".format(appname, desc) % dict(appname=app.name)


def get_require_perm_names(appname, permission=None):
    """获取依赖的django权限"""
    rv = set()
    perms = (permission_required.get(permission, []) if permission
        else permission_required.keys())
    for perm in perms:
        if perm.startswith("wechat_django."):
            rv.add(perm)
        else:
            rv.update(get_require_perm_names(appname, perm))
    return rv


def get_perm_model(perm_name):
    """由permission获取permission model"""
    try:
        applabel, codename = perm_name.split(".")
    except:
        applabel = "wechat_django"
        codename = perm_name
    return Permission.objects.get(
        codename=codename,
        content_type__app_label=applabel
    )


def get_perms_by_codenames(codenames):
    return (Permission.objects
        .filter(content_type__app_label="wechat_django")
        .filter(codename__in=codenames)
        .all())


@receiver(m.signals.m2m_changed, sender=Group.permissions.through)
@receiver(m.signals.m2m_changed, sender=User.user_permissions.through)
def add_required_perms(sender, instance, action, *args, **kwargs):
    if action == "pre_add":
        if isinstance(instance, User):
            perms_set = instance.user_permissions
        else:
            perms_set = instance.permissions
        # 检查相关权限
        perm_names = set()
        perms = Permission.objects.filter(id__in=kwargs["pk_set"]).all()
        for perm in perms:
            appname, permission = match_permission(perm.codename)
            if appname:
                perm_names.update(
                    get_require_perm_names(appname, permission))
        if perm_names:
            codenames = list(map(lambda o: o.split(".")[1], perm_names))
            perms_set.add(*get_perms_by_codenames(codenames))


def get_user_permissions(user, app=None):
    """列举用户所有的微信权限
    :type user: django.contrib.auth.models.User
    """
    perm_names = user.get_all_permissions()
    rv = defaultdict(set)
    for perm_name in perm_names:
        appname, permission = match_permission(perm_name)
        if appname:
            if permission:
                rv[appname].add(permission)
            else:
                # 所有权限
                rv[appname] = set(permissions.keys())
    return rv[app.name] if app else dict(rv.items())


def match_permission(perm_name):
    """从permission的codename中拿到appname与权限名"""
    str4format = r"(?:{label}[.])?{prefix}(?P<appname>.+?)(?:|(?P<permission>.+))?$"
    pattern = str4format.format(
        label="wechat_django",
        prefix=WECHATPERM_PREFIX
    ).replace("|", "[|]")
    match = re.match(pattern, perm_name)
    if match:
        return match.group("appname"), match.group("permission")
    else:
        return None, None


def migrate_permissions(permissions):
    pass
