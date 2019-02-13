from collections import defaultdict
import itertools
import re

from django.contrib.auth.models import ContentType, Group, Permission, User
from django.db import models as m
from django.dispatch import receiver

WECHATPERM_PREFIX = "app|"

permissions = {
    "manage": "can manage {appname}",
    "article": "can edit {appname} articles",
    "article_sync": "can sync {appname} articles",
    "material": "can edit {appname} materials",
    "material_sync": "can sync {appname} materials",
    "menu": "can edit {appname} menus",
    "menu_sync": "can sync {appname} menus",
    "menu_publish": "can publish {appname} menus",
    "messagehandler": "can edit {appname} message handlers",
    "messagehandler_sync": "can sync {appname} message handlers",
    "messagelog": "can view {appname} message logs",
    "user": "can edit {appname} users",
    "user_sync": "can sync {appname} users",
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


def list_permissions(app):
    """列举该app下的所有权限"""
    rv = set()
    rv.add("{prefix}{appname}".format(
        prefix=WECHATPERM_PREFIX,
        appname=app.name
    ))
    rv.update(
        "{prefix}{appname}|{perm}".format(
            prefix=WECHATPERM_PREFIX,
            appname=app.name,
            perm=perm
        )
        for perm in permissions
    )
    return rv


def get_user_permissions(user, app=None):
    """列举用户所有的微信权限
    :type user: django.contrib.auth.models.User
    """
    perms = user.get_all_permissions()
    rv = defaultdict(set)
    for permission in perms:
        appname, perm = match_perm(permission)
        if appname:
            if perm:
                rv[appname].add(perm)
            else:
                # 所有权限
                rv[appname] = set(permissions.keys())
    return rv[app.name] if app else dict(rv.items())


def get_permission_desc(permission, appname):
    appname, perm = match_perm(permission)
    desc = permissions[perm] if perm else "can full control {appname}"
    return "{0} | {1}".format(appname, desc)


@receiver(m.signals.m2m_changed, sender=Group.permissions.through)
@receiver(m.signals.m2m_changed, sender=User.user_permissions.through)
def before_permission_change(sender, instance, action, *args, **kwargs):
    if action == "pre_add":
        from . import WeChatApp
        if isinstance(instance, User):
            permissions = instance.user_permissions
        else:
            permissions = instance.permissions
        # 检查相关权限
        needed_perms = set()
        perms = Permission.objects.filter(id__in=kwargs["pk_set"]).all()
        for permission in perms:
            appname, perm = match_perm(permission.codename)
            if appname:
                needed_perms.update(get_require_permissions(appname, perm))
        if needed_perms:
            codenames = list(map(lambda o: o.split(".")[1], needed_perms))
            permissions.add(*Permission.objects
                .filter(content_type__app_label="wechat_django")
                .filter(codename__in=codenames)
                .all())


def get_require_permissions(appname, perm=None):
    """获取依赖的django权限"""
    rv = set()
    perms = (permission_required.get(perm, []) if perm else
        permission_required.keys())
    for perm in perms:
        if perm.startswith("wechat_django."):
            rv.add(perm)
        else:
            rv.update(get_require_permissions(appname, perm))
    return rv


def match_perm(perm):
    """从permission的codename中拿到appname与权限名"""
    pattern = r"(?:{label}[.])?{prefix}(?P<appname>.+?)(?:|(?P<perm>.+))?$".format(
        label="wechat_django",
        prefix=WECHATPERM_PREFIX
    ).replace("|", "[|]")
    match = re.match(pattern, perm)
    if match:
        return match.group("appname"), match.group("perm")
    else:
        return None, None

