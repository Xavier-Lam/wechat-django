# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.conf.urls import url
from django.contrib import admin
from django.template.response import SimpleTemplateResponse
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from ..admin.base import registered_admins, WeChatModelAdmin
from ..models import WeChatApp
from ..models.permission import get_user_permissions
from ..utils.admin import get_request_params
from .wechat import default_site as default_wechat_site


def wechat_admin_view(view, site):
    """装饰WeChatAdmin中的view
    在请求上附上WeChatApp实例
    并在响应的模板上附上app,app_id等context
    """
    @wraps(view)
    def decorated_func(request, *args, **kwargs):
        model_admin = getattr(view, "__self__", None)

        # 从请求中获取app,附在request上
        app = None
        app_id = get_request_params(request, "app_id")
        if app_id:
            try:
                app = site.wechat_site.app_queryset.get(id=app_id)
            except WeChatApp.DoesNotExist:
                pass
        request.app_id = app_id
        request.app = app

        rv = view(request, *args, **kwargs)

        # 更新response的context
        if isinstance(rv, SimpleTemplateResponse):
            if rv.context_data is None:
                rv.context_data = dict()
            rv.context_data.update(
                app=app,
                app_id=app_id
            )

        return rv

    return decorated_func


class WeChatAdminSiteMixin(object):
    """AdminSiteMixin 自定义后台需要包含微信相关功能时 需要将本Mixin混入"""
    _default_wechat_site = default_wechat_site

    def __init__(self, *args, **kwargs):
        super(WeChatAdminSiteMixin, self).__init__(*args, **kwargs)
        for model, admin_class in registered_admins:
            self.register(model, admin_class)

    @property
    def wechat_site(self):
        """默认微信站点,在获取app queryset时与做url reverse时需使用

        :rtype: wechat_django.WeChatSite
        """
        return self._default_wechat_site

    def admin_view(self, view, cacheable=False):
        model_admin = getattr(view, "__self__", None)

        if isinstance(model_admin, WeChatModelAdmin):
            view = wechat_admin_view(view, self)

        return super(WeChatAdminSiteMixin, self).admin_view(view, cacheable)

    def get_urls(self):
        rv = super(WeChatAdminSiteMixin, self).get_urls()

        wechat_app_index = wechat_admin_view(self.wechat_index, self)
        rv += [
            url(
                r"(?P<app_label>wechat_django)/apps/(?P<app_id>\d+)/$",
                self.admin_view(wechat_app_index),
                name="wechat_funcs_list"
            )
        ]

        return rv

    def _build_app_dict(self, request, label=None):
        rv = super(WeChatAdminSiteMixin, self)._build_app_dict(request, label)

        if not label:
            # 首页 追加app列表
            app_dict = self._build_wechat_app_dict(request)
            if app_dict["has_module_perms"]:
                rv["wechat_django_apps"] = app_dict
        elif not rv:
            pass
        elif label == "wechat_django":
            app_id = request.resolver_match.kwargs.get("app_id")
            if app_id:
                # 公众号首页,各管理菜单
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
            else:
                # 原始菜单(只有app管理)
                pass

        return rv

    def _build_wechat_app_dict(self, request):
        """构建wechat app列表菜单"""
        query = self.wechat_site.app_queryset
        if not request.user.is_superuser:
            perms = get_user_permissions(request.user)
            allowed_apps = {
                k for k, ps in perms.items() if ps != {"manage"}
            }
            query = query.filter(name__in=allowed_apps)
        apps = query.all()
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
                        app_label="wechat_django"
                    )
                )
            )
            for app in apps
        ]
        return {
            'name': _("WeChat apps"),
            'app_label': "wechat_django",
            # 'app_url': "#", # TODO: 修订app_url
            'has_module_perms': bool(app_perms),
            'models': app_perms,
        }

    def wechat_index(self, request, *args, **kwargs):
        """某个公众号后台管理首页"""
        kwargs.pop("app_id", None)
        return super(WeChatAdminSiteMixin, self).app_index(
            request, *args, **kwargs)


class WeChatAdminSite(WeChatAdminSiteMixin, admin.AdminSite):
    pass


def patch_admin():
    """用当前wechat-django默认的adminsite替代django自带的默认adminsite"""
    setattr(admin.sites, "site", default_site)
    setattr(admin, "site", default_site)


default_site = WeChatAdminSite()
default_site._registry.update(admin.sites.site._registry)
