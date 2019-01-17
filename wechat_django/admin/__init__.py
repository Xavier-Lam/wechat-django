from django.conf import settings
from django.conf.urls import url, include
from django.urls import NoReverseMatch, reverse
from django.utils.http import urlencode
from django.utils.module_loading import import_string

def patch_admin(admin):
    """
    :type admin: django.contrib.admin.sites.AdminSite
    """
    from ..apps import WechatConfig
    from ..models import WechatApp
    from .bases import WechatAdmin
    app_label = WechatConfig.name
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
                        model['add_url'] += "?" + urlencode(dict(app_id=app_id))
            else:
                # 原始菜单
                pass
        # TODO: 可能需要考虑app_dict不存在的情况

        return rv

    def _build_wechat_app_dict(self, request):
        apps = WechatApp.objects.all()
        return {
            'name': app_label,
            'app_label': app_label,
            # 'app_url': "#", # TODO: 修订app_url
            'has_module_perms': True, # TODO: 修订权限
            'models': [
                dict(
                    name=str(app),
                    object_name=app.name,
                    perms=dict(
                        change=True, # TODO: 修订权限
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
            ],
        }

    def get_urls(self):
        rv = origin_get_urls(self)
        
        rv += [url(
            r"^(?P<app_label>%s)/apps/(?P<app_id>\d+)/$"%app_label, 
            wechat_index,
            name="wechat_funcs_list"
        )]

        return rv

    import types
    admin._build_app_dict = types.MethodType(_build_app_dict, admin)
    admin.get_urls = types.MethodType(get_urls, admin)

admin_site_paths = getattr(settings, "ADMINSITE", "django.contrib.admin.site")
if not isinstance(admin_site_paths, list):
    admin_site_paths = [admin_site_paths]
for site in admin_site_paths:
    admin = import_string(site)
    patch_admin(admin)

from . import wechatapp, menu, messagehandler