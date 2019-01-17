from functools import update_wrapper

from django.conf import settings
from django.conf.urls import url, include
from django.urls import NoReverseMatch, reverse
from django.utils.module_loading import import_string

def patch_admin(admin):
    """
    :type admin: django.contrib.admin.sites.AdminSite
    """
    from ..apps import WechatConfig
    from ..models import WechatApp
    wechat_django_app_label = WechatConfig.name
    wechat_django_apps_app_label = "wechat_django_apps"

    origin_build_app_dict = admin.__class__._build_app_dict
    origin_get_urls = admin.__class__.get_urls

    def wechat_index(request, *args, **kwargs):
        kwargs.pop("app_id", None)
        return admin.app_index(request, *args, **kwargs)

    def _build_app_dict(self, request, label=None):
        rv = origin_build_app_dict(self, request, label)
        # print(label)

        if not label:
            rv[wechat_django_apps_app_label] = _build_wechat_app_dict(self, request)
        elif label == wechat_django_apps_app_label:
            return _build_wechat_app_dict(self, request)
        
        # app_id = request.resolver_match.kwargs.get("app_id")
        # if app_id:
        #     # 显示功能
        #     # 去除wechat app
        #     if label:
        #         rv["models"] = list(filter(
        #             lambda o: o["object_name"] != WechatApp.__name__, 
        #             rv["models"]
        #         ))
        #         # admin url和add url
        #         for model in rv["models"]:
        #             if model["perms"].get("change"):
        #                 try:
        #                     model['admin_url'] = reverse(
        #                         'admin:%s_%s_changelist' % (app_label, "menu"), 
        #                         current_app=self.name,
        #                         kwargs=dict(app_id=app_id)
        #                     )
        #                 except NoReverseMatch:
        #                     pass
        #             if model["perms"].get("add"):
        #                 try:
        #                     model['add_url'] = reverse(
        #                         'admin:%s_%s_add' % (app_label, "menu"), 
        #                         current_app=self.name, 
        #                         kwargs=dict(app_id=app_id)
        #                     )
        #                 except NoReverseMatch:
        #                     pass
        # else:
        #     # 显示微信号列表
        #     pass
        # # 追加wechat app
        # # TODO: 可能需要考虑app_dict不存在的情况

        return rv

    def _build_wechat_app_dict(self, request):
        apps = WechatApp.objects.all()
        return {
            'name': wechat_django_apps_app_label,
            'app_label': wechat_django_apps_app_label,
            # 'app_url': reverse(
            #     'admin:app_list',
            #     kwargs={'app_label': wechat_django_apps_app_label},
            #     current_app=self.name,
            # ),
            'has_module_perms': True, # TODO: 修订权限
            'models': [
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
                            app_label=wechat_django_app_label
                        )
                    )
                )
                for app in apps
            ],
        }

    def _wechat_admin_iters(admin):
        return (
            (model, model_admin)
            for model, model_admin in admin._registry.items()
            if isinstance(model_admin, WechatAdminMixin)
        )

    def get_urls(self):
        rv = origin_get_urls(self)

        # 重新注册所有wechatadmin url
        registered_urls = [
            rule for rule in rv
            if rule.regex.pattern.startswith(r"^%s/"%wechat_django_app_label)
            and not rule.regex.pattern.startswith(r"^%s/%s"%(wechat_django_app_label, wechatapp.WechatApp._meta.model_name))
        ]
        # 移除原有pattern
        rv = list(set(rv)^set(registered_urls))
        # 添加包含app_id的wechatadmin url
        rv += [
            url(
                r"^%s/(?P<app_id>\d+)/%s/" % (wechat_django_app_label, model._meta.model_name), 
                include(model_admin.urls)
            )
            for model, model_admin in _wechat_admin_iters(self)
        ]        

        # 注册微信号首页
        def wrap(view, cacheable=False):
            def wrapper(*args, **kwargs):
                return self.admin_view(view, cacheable)(*args, **kwargs)
            wrapper.admin_site = self
            return update_wrapper(wrapper, view)
        # TODO: 修订app_label
        rv += [url(
            r"^%s/(?P<app_id>\d+)/\?app_label=(?P<app_label>%s)$"%(wechat_django_apps_app_label, wechat_django_app_label), 
            wechat_index,
            name="wechat_funcs_list"
        )]

        return rv

    import types
    admin._build_app_dict = types.MethodType(_build_app_dict, admin)
    admin.get_urls = types.MethodType(get_urls, admin)

admin_obj = getattr(settings, "ADMINOBJECT", "django.contrib.admin.site")
admin = import_string(admin_obj)
patch_admin(admin)

from . import wechatapp, menu, messagehandler
from .bases import WechatAdminMixin