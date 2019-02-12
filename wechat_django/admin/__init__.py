from django.utils.module_loading import import_string

from .. import settings

def patch_admin(admin):
    """
    :type admin: django.contrib.admin.sites.AdminSite
    """
    import re
    import types

    from django.conf.urls import url, include
    from django.urls import NoReverseMatch, reverse
    from django.utils.http import urlencode

    from ..apps import WeChatConfig
    from ..models import WeChatApp
    from ..models.permission import get_user_permissions
    from .bases import WeChatAdmin

    app_label = WeChatConfig.name
    fake_app_label = app_label + "_apps"

    origin_build_app_dict = admin.__class__._build_app_dict
    origin_get_urls = admin.__class__.get_urls

    def wechat_index(request, *args, **kwargs):
        kwargs.pop("app_id", None)
        return admin.app_index(request, *args, **kwargs)

    def _build_app_dict(self, request, label=None):
        rv = origin_build_app_dict(self, request, label)

        if not label:
            # 追加app列表
            rv[fake_app_label] = _build_wechat_app_dict(self, request)
        elif label == app_label:
            app_id = request.resolver_match.kwargs.get("app_id")
            if app_id:
                # 管理菜单
                for model in rv["models"]:
                    if model["perms"].get("change") and model.get("admin_url"):
                        model['admin_url'] += "?" + urlencode(dict(app_id=app_id))
                    if model["perms"].get("add") and model.get("add_url"):
                        query = urlencode(dict(
                            _changelist_filters=urlencode(dict(
                                app_id=app_id
                            ))
                        ))
                        model['add_url'] += "?" + query
                        # TODO: 修改add_url
            else:
                # 原始菜单
                pass
                
        return rv

    def _build_wechat_app_dict(self, request):
        if request.user.is_superuser:
            apps = WeChatApp.objects.all()
        else:
            perms = get_user_permissions(request.user)
            allowed_apps = perms.keys()
            apps = WeChatApp.objects.filter(name__in=allowed_apps)
        app_perms = [
            dict(
                name=str(app),
                object_name=app.name,
                perms=dict(
                    change=True,
                ),
                admin_url=reverse(
                    'admin:wechat_funcs_list', 
                    current_app=self.name,
                    kwargs=dict(
                        app_id=app.id,
                        app_label=app_label
                    )
                )
            )
            for app in apps
        ]
        return {
            'name': app_label,
            'app_label': app_label,
            # 'app_url': "#", # TODO: 修订app_url
            'has_module_perms': bool(app_perms),
            'models': app_perms,
        }

    def get_urls(self):
        rv = origin_get_urls(self)
        
        rv += [url(
            r"^(?P<app_label>%s)/apps/(?P<app_id>\d+)/$"%app_label, 
            wechat_index,
            name="wechat_funcs_list"
        )]

        return rv

    admin._build_app_dict = types.MethodType(_build_app_dict, admin)
    admin.get_urls = types.MethodType(get_urls, admin)

admin_site_paths = settings.ADMINSITE
if not isinstance(admin_site_paths, (list, tuple)):
    admin_site_paths = [admin_site_paths]
for site in admin_site_paths:
    admin = import_string(site)
    patch_admin(admin)

from . import (wechatapp, user, menu, messagehandler, messagelog, 
    material, article)