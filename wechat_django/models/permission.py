import itertools
import re

from django.contrib.auth.models import ContentType, Group, Permission, User
from django.db import models as m
from django.dispatch import receiver

WECHATPERM_PREFIX = "app|"

permissions = (
    "manage",
    "article",
    "article_sync",
    "material",
    "material_sync",
    "menu",
    "menu_sync",
    "menu_publish",
    "messagehandler",
    "messagehandler_sync",
    "messagelog",
    "user",
    "user_sync",
)

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
        pattern = r"{prefix}(?P<appname>.+)(?:|(?P<perm>.+))?$".format(
            prefix=WECHATPERM_PREFIX
        ).replace("|", "[|]")
        needed_perms = set()
        perms = Permission.objects.filter(id__in=kwargs["pk_set"]).all()
        for permission in perms:
            match = re.match(pattern, permission.codename)
            if match:
                appname = match.group("appname")
                perm = match.group("perm")
                needed_perms.update(_get_require_permissions(appname, perm))
        if needed_perms:
            codenames = list(map(lambda o: o.split(".")[1], needed_perms))
            permissions.add(*Permission.objects
                .filter(content_type__app_label="wechat_django")
                .filter(codename__in=codenames)
                .all())

def _get_require_permissions(appname, perm=None):
    rv = set()
    perms = (permission_required.get(perm, []) if perm else 
        permission_required.keys())
    for perm in perms:
        if perm.startswith("wechat_django."):
            rv.add(perm)
        else:
            # rv.add("{label}.{prefix}{appname}|{perm}".format(
            #     label="wechat_django",
            #     prefix=WECHATPERM_PREFIX,
            #     appname=appname,
            #     perm=perm
            # ))
            rv.update(_get_require_permissions(appname, perm))
    return rv

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