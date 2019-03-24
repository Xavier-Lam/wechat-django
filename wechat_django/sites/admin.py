# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from contextlib import contextmanager
from functools import wraps

from django.conf.urls import include, url
from django.contrib import admin
from django.http import response
from django.template.response import SimpleTemplateResponse
from django.urls import NoReverseMatch, resolve, reverse
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
        if "wechat_app_id" not in kwargs:
            return response.HttpResponseNotFound()

        # 对于只有object_id没有app_id的 重定向到有app_id的url
        app_id = kwargs.pop("wechat_app_id", None)
        object_id = kwargs.get("object_id", None)
        if object_id and not app_id:
            modeladmin = view.__self__
            try:
                obj = modeladmin.model.objects.get(pk=object_id)
            except modeladmin.model.DoesNotExist:
                return response.HttpResponseBadRequest()

            url_name = resolve(request.path_info).url_name
            return response.HttpResponseRedirect(
                reverse("admin:" + url_name, kwargs=dict(
                    wechat_app_id=obj.app_id,
                    object_id=object_id
                ))
            )

        extra_context = kwargs.pop("extra_context", None) or {}
        try:
            # 附上app
            app = site.wechat_site.app_queryset.get(id=app_id)
            request.app = app
            request.app_id = app_id
            # 增加模板context
            extra_context = dict(
                wechat_app=app,
                wechat_app_id=app_id
            )
        except WeChatApp.DoesNotExist:
            return response.HttpResponseNotFound()

        kwargs["extra_context"] = extra_context
        return view(request, *args, **kwargs)

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

    @contextmanager
    def _unregister_wechatadmins(self):
        """暂时取消注册wechat-django相关的modeladmin以进行一些操作"""
        for model, model_admin in registered_admins:
            self.unregister(model)
        yield
        for model, model_admin in registered_admins:
            self.register(model, model_admin)

    def _iter_wechatadmins(self):
        """枚举所有的wechat-django modeladmin实例"""
        for model, model_admin in registered_admins:
            yield model, self._registry[model]

    def admin_view(self, view, cacheable=False):
        # 对于wechat-django相关的admin view 做一下装饰
        admin = getattr(view, "__self__", None)
        if isinstance(admin, WeChatModelAdmin):
            view = wechat_admin_view(view, self)

        return super(WeChatAdminSiteMixin, self).admin_view(view, cacheable)

    def get_urls(self):
        with self._unregister_wechatadmins():
            urlpatterns = super(WeChatAdminSiteMixin, self).get_urls()

        # 重新注册wechat_django相关的modeladmin
        for model, model_admin in self._iter_wechatadmins():
            info = model._meta.app_label, model._meta.model_name
            urlpatterns += [
                url(
                    r"^%s/(?:(?P<wechat_app_id>\d+)/)?%s/" % info,
                    include(model_admin.urls)
                ),
            ]

        urlpatterns += [
            url(
                r"(?P<app_label>wechat_django)/apps/(?P<wechat_app_id>\d+)/$",
                self.admin_view(wechat_admin_view(self.wechat_index, self)),
                name="wechat_funcs_list"
            )
        ]

        return urlpatterns

    def _build_app_dict(self, request, label=None):
        app_id = getattr(request, "app_id", None)
        if app_id:
            # 微信相关模块
            app_label = WeChatApp._meta.app_label
            rv = dict(
                name=WeChatApp._meta.verbose_name_plural,
                app_label=app_label,
                app_url=reverse(
                    "admin:wechat_funcs_list",
                    current_app=self.name,
                    kwargs=dict(
                        wechat_app_id=app_id,
                        app_label=app_label
                    )
                ),
                has_module_perms=True, # TODO: 修正
                models=[]
            )

            for model, model_admin in self._iter_wechatadmins():
                info = (app_label, model._meta.model_name)
                perms = model_admin.get_model_perms(request)
                model_dict = {
                    'name': model._meta.verbose_name_plural,
                    'object_name': model._meta.object_name,
                    'perms': perms,
                }
                if perms.get('change'):
                    try:
                        model_dict['admin_url'] = reverse(
                            'admin:%s_%s_changelist' % info,
                            current_app=self.name,
                            kwargs=dict(wechat_app_id=app_id)
                        )
                    except NoReverseMatch:
                        pass
                if perms.get('add'):
                    try:
                        model_dict['add_url'] = reverse(
                            'admin:%s_%s_add' % info,
                            current_app=self.name,
                            kwargs=dict(wechat_app_id=app_id)
                        )
                    except NoReverseMatch:
                        pass
                rv["models"].append(model_dict)
            
            if not label:
                return {app_label: rv}
        else:
            with self._unregister_wechatadmins():
                rv = super(WeChatAdminSiteMixin, self)._build_app_dict(request, label)
            
            # 首页, 增加app列表
            if not label:
                app_dict = self._build_wechat_app_dict(request)
                if app_dict["has_module_perms"]:
                    rv["wechat_django_apps"] = app_dict

        return rv

    def _build_wechat_app_dict(self, request):
        """构建wechat apps列表"""
        app_label = WeChatApp._meta.app_label

        # 过滤权限
        query = self.wechat_site.app_queryset
        if not request.user.is_superuser:
            perms = get_user_permissions(request.user)
            allowed_apps = {
                k for k, ps in perms.items() if ps != {"manage"}
            }
            query = query.filter(name__in=allowed_apps)
        apps = query.all()

        # 构建app_dict
        app_perms = [
            dict(
                name=str(app),
                object_name=app.name,
                perms=dict(
                    change=True,
                ),
                admin_url=reverse(
                    "admin:wechat_funcs_list",
                    current_app=self.name,
                    kwargs=dict(
                        wechat_app_id=app.id,
                        app_label=app_label
                    )
                )
            )
            for app in apps
        ]
        return {
            'name': WeChatApp._meta.verbose_name_plural,
            'app_label': app_label,
            # 'app_url': "#", # TODO: 修订app_url
            'has_module_perms': bool(app_perms),
            'models': app_perms,
        }

    def wechat_index(self, request, *args, **kwargs):
        """某个公众号后台管理首页"""
        return super(WeChatAdminSiteMixin, self).app_index(
            request, *args, **kwargs)


class WeChatAdminSite(WeChatAdminSiteMixin, admin.AdminSite):
    pass


def patch_admin():
    """用当前wechat-django默认的adminsite替代django自带的默认adminsite"""
    default_site._registry.update(admin.sites.site._registry)
    setattr(admin.sites, "site", default_site)
    setattr(admin, "site", default_site)


default_site = WeChatAdminSite()
