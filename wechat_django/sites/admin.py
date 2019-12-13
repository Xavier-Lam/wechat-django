# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from contextlib import contextmanager
from functools import wraps

from django.conf.urls import include, url
from django.contrib import admin
from django.http import response
from django.urls import NoReverseMatch, resolve, Resolver404, reverse
from object_tool import CustomObjectToolAdminSiteMixin
from six.moves.urllib.parse import urlparse

from ..admin.base import registered_admins, WeChatModelAdmin
from ..models import WeChatApp
from ..models.permission import get_user_permissions
from .wechat import default_site as default_wechat_site


def wechat_admin_view(view, site):
    """装饰WeChatAdmin中的view
    在请求上附上WeChatApp实例
    并在响应的模板上附上app,app_id等context
    """

    def fix_url(request, object_id):
        """修正请求url

        因为某些特殊原因(比如说第三方模块),导致访问地址错误,尽可能修正错误
        """
        resolved_url = resolve(request.path_info)
        kwargs = resolved_url.kwargs

        if object_id:
            # 对于只有object_id没有app_id的 重定向到有app_id的url
            modeladmin = view.__self__
            try:
                obj = modeladmin.model.objects.get(pk=object_id)
            except modeladmin.model.DoesNotExist:
                return response.HttpResponseNotFound()
            app_id = obj.app_id
        else:
            # 对于没有app_id的listview请求 优先取referrer的app_id
            referrer = request.META.get("HTTP_REFERER", "")
            path_info = urlparse(referrer).path
            try:
                app_id = resolve(path_info).kwargs["wechat_app_id"]
            except (KeyError, Resolver404):
                return response.HttpResponseNotFound()
            # 可能会发生url_kwargs中object_id为None的情况
            # 此处做排除,否则可能会发生重定向错误
            if "object_id" in kwargs and kwargs["object_id"] is None:
                del kwargs["object_id"]

        kwargs.update(wechat_app_id=app_id)
        fixed_url = reverse("admin:" + resolved_url.url_name, kwargs=kwargs)
        return response.HttpResponseRedirect(fixed_url, status=307)

    @wraps(view)
    def decorated_func(request, *args, **kwargs):
        """给request及context带上app和appid"""
        app_id = kwargs.pop("wechat_app_id", None)
        object_id = kwargs.get("object_id", None)
        if not app_id:
            return fix_url(request, object_id)

        extra_context = kwargs.pop("extra_context", None) or {}
        try:
            app = site.wechat_site.app_queryset.get(id=app_id)
        except WeChatApp.DoesNotExist:
            return response.HttpResponseNotFound()

        # 附上app
        request.app = app
        request.app_id = app_id
        # 增加模板context
        extra_context.update(
            wechat_app=app,
            wechat_app_id=app_id
        )
        kwargs["extra_context"] = extra_context
        return view(request, *args, **kwargs)

    return decorated_func


class WeChatAdminSiteMixin(CustomObjectToolAdminSiteMixin):
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
        unregistered = []
        for model, model_admin in registered_admins:
            if model in self._registry:
                self.unregister(model)
                unregistered.append(model)
        yield
        for model, model_admin in registered_admins:
            if model in unregistered:
                self.register(model, model_admin)

    def _iter_wechatadmins(self, request=None):
        """枚举所有的wechat-django modeladmin实例

        要对某app增加或者移除模型时,请复写方法,判断request不为空时,做额外处理
        """
        for model, model_admin in registered_admins:
            yield model, self._registry[model]

    def admin_view(self, view, cacheable=False):
        model_admin = getattr(view, "__self__", None)
        # 对于wechat-django相关的admin view 做一下装饰
        if isinstance(model_admin, WeChatModelAdmin):
            view = wechat_admin_view(view, self)
            model_admin.wechat_site = self.wechat_site

        return super(WeChatAdminSiteMixin, self).admin_view(view, cacheable)

    def get_urls(self):
        # 不注册WeChatModel的url
        with self._unregister_wechatadmins():
            urlpatterns = super(WeChatAdminSiteMixin, self).get_urls()

        # 注册WeChatModel的url,这些url是依赖不同WeChatApp的
        for model, model_admin in self._iter_wechatadmins():
            info = model._meta.app_label, model._meta.model_name
            urlpatterns += [
                url(
                    r"^%s/(?:(?P<wechat_app_id>\d+)/)?%s/" % info,
                    include(model_admin.urls)
                ),
            ]

        # 注册某个WeChatApp后台管理首页
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
            # 某WeChatApp下的菜单
            rv = self._build_wechat_func_dict(request)

            if not label:
                return {WeChatApp._meta.app_label: rv}
        else:
            # 首页或其他模块菜单 不注册WeChatModel的后台
            with self._unregister_wechatadmins():
                parent = super(WeChatAdminSiteMixin, self)
                rv = parent._build_app_dict(request, label)

            # 首页, 增加app列表
            if not label:
                app_dict = self._build_wechat_app_dict(request)
                if app_dict["has_module_perms"]:
                    rv["wechat_django_apps"] = app_dict

        return rv

    def _build_wechat_app_dict(self, request):
        """构建wechat apps列表"""
        app_label = WeChatApp._meta.app_label

        # 过滤有权限的app
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
                ),
                add_url=None,
                view_only=False  # TODO: 改为去编辑app页面
            )
            for app in apps
        ]
        return {
            'name': WeChatApp._meta.verbose_name_plural,
            'app_label': app_label,
            'app_url': "#",
            'has_module_perms': bool(app_perms),
            'models': app_perms,
        }

    def _build_wechat_func_dict(self, request):
        """构建某一公众号下功能列表"""
        has_module_perms = get_user_permissions(request.user, request.app,
                                                exclude_manage=True,
                                                exclude_sub=True)
        if not has_module_perms:
            return None

        app_id = request.app_id
        app_label = WeChatApp._meta.app_label
        rv = dict(
            name=str(request.app),
            app_label=app_label,
            app_url=reverse(
                "admin:wechat_funcs_list",
                current_app=self.name,
                kwargs=dict(
                    wechat_app_id=app_id,
                    app_label=app_label
                )
            ),
            has_module_perms=True,
            models=[]
        )

        for model, model_admin in self._iter_wechatadmins(request):
            # 构建每个app下的功能菜单
            info = (model._meta.app_label, model._meta.model_name)
            perms = model_admin.get_model_perms(request)
            if not perms:
                continue
            model_dict = dict(
                name=model._meta.verbose_name_plural,
                object_name=model._meta.object_name,
                perms=perms,
                admin_url=None,
                add_url=None,
                view_only=False
            )
            if perms.get("change"):
                try:
                    model_dict["admin_url"] = reverse(
                        "admin:%s_%s_changelist" % info,
                        current_app=self.name,
                        kwargs=dict(wechat_app_id=app_id)
                    )
                except NoReverseMatch:
                    pass
            if perms.get("add"):
                try:
                    model_dict["add_url"] = reverse(
                        "admin:%s_%s_add" % info,
                        current_app=self.name,
                        kwargs=dict(wechat_app_id=app_id)
                    )
                except NoReverseMatch:
                    pass
            rv["models"].append(model_dict)

        return rv

    def wechat_index(self, request, *args, **kwargs):
        """某个WeChatApp后台管理首页"""
        return super(WeChatAdminSiteMixin, self).app_index(request, *args,
                                                           **kwargs)


class WeChatAdminSite(WeChatAdminSiteMixin, admin.AdminSite):
    def from_site(self, site):
        self._registry.update(site._registry)
        for model, model_admin in self._registry.items():
            model_admin.admin_site = self


def patch_admin():
    """用当前wechat-django默认的adminsite替代django自带的默认adminsite"""
    default_site.from_site(admin.site)
    setattr(admin.sites, "site", default_site)
    setattr(admin, "site", default_site)


default_site = WeChatAdminSite()
