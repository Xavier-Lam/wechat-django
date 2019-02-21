# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import types

from django import forms
from django.conf.urls import url
from django.contrib import admin
from django.contrib.admin.templatetags import admin_list
from django.contrib.admin.views.main import ChangeList as _ChangeList
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
import six
from six.moves.urllib.parse import parse_qsl

from ..apps import WeChatConfig
from ..models import WeChatApp
from ..models.permission import get_user_permissions
from ..utils.web import mutable_GET


registered_admins = []


@admin_list.register.inclusion_tag('admin/wechat_django/search_form.html')
def search_form(cl):
    """
    搜索form带app_id
    """
    return admin_list.search_form(cl)


def has_wechat_permission(request, app, category="", operate="", obj=None):
    """
    检查用户是否具有某一微信权限
    :type request: django.http.request.HttpRequest
    """
    if request.user.is_superuser:
        return True
    perms = get_user_permissions(request.user, app)
    needs = {category, "{0}_{1}".format(category, operate)}
    return bool(needs.intersection(perms))


class ChangeList(_ChangeList):
    def __init__(self, request, *args, **kwargs):
        # app_id在changelist中会抛出IncorrectLookupParameters异常
        self.app_id = request.GET.get("app_id")
        with mutable_GET(request) as GET:
            GET.pop("app_id", None)

        super(ChangeList, self).__init__(request, *args, **kwargs)

        with mutable_GET(request) as GET:
            GET["app_id"] = self.app_id

    def get_query_string(self, new_params=None, remove=None):
        # filter的链接会掉querystring
        query = super(ChangeList, self).get_query_string(new_params, remove).replace("?", "&")
        prefix = "?app_id={0}".format(self.app_id)
        return prefix + query


class WeChatAdminMetaClass(forms.MediaDefiningClass):
    def __new__(cls, name, bases, attrs):
        self = super(WeChatAdminMetaClass, cls).__new__(
            cls, name, bases, attrs)
        if name != "WeChatAdmin":
            registered_admins.append(self)
        return self


class WeChatAdmin(six.with_metaclass(WeChatAdminMetaClass, admin.ModelAdmin)):
    def changelist_view(self, request, extra_context=None):
        # 允许没有选中的actions
        post = request.POST.copy()
        if admin.helpers.ACTION_CHECKBOX_NAME not in post:
            post.update({admin.helpers.ACTION_CHECKBOX_NAME: None})
            request._set_post(post)
        extra_context = self._update_context(request, extra_context)
        return super(WeChatAdmin, self).changelist_view(request, extra_context)

    def history_view(self, request, object_id, extra_context=None):
        extra_context = self._update_context(request, extra_context)
        return super(WeChatAdmin, self).history_view(
            request, object_id, extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        extra_context = self._update_context(request, extra_context)
        return super(WeChatAdmin, self).delete_view(
            request, object_id, extra_context)

    def changeform_view(
        self, request, object_id=None, form_url="", extra_context=None):
        if object_id and not self.get_app(request, True):
            # 对于没有app_id的请求,重定向至有app_id的地址
            obj = self.model.objects.get(id=object_id)
            app_id = getattr(obj, "app_id", obj.app.id)
            return redirect(request.path + "?" + urlencode(dict(
                _changelist_filters="app_id=" + str(app_id)
            )), permanent=True)
        form_url = form_url or "?{0}".format(request.GET.urlencode())
        return super(WeChatAdmin, self).changeform_view(
            request, object_id, form_url, extra_context)

    def render_change_form(self, request, context, *args, **kwargs):
        context = self._update_context(request, context)
        return super(WeChatAdmin, self).render_change_form(
            request, context, *args, **kwargs)

    def get_changelist(self, request, **kwargs):
        return ChangeList

    def _update_context(self, request, context):
        app = self.get_app(request)
        context = context or dict()
        context.update(dict(
            app_id=app.id,
            app=app
        ))
        return context

    def get_queryset(self, request):
        self.request = request
        rv = super(WeChatAdmin, self).get_queryset(request)
        app_id = self.get_app(request).id
        return self._filter_app_id(rv, app_id) if app_id else rv.none()

    def get_preserved_filters(self, request):
        with mutable_GET(request) as GET:
            GET["app_id"] = self.get_app(request).id
            try:
                return super(WeChatAdmin, self).get_preserved_filters(request)
            finally:
                GET.pop("app_id", None)

    def _filter_app_id(self, queryset, app_id):
        return queryset.filter(app_id=app_id)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = self.get_app(request).id
        return super(WeChatAdmin, self).save_model(request, obj, form, change)

    def get_model_perms(self, request):
        # 隐藏首页上的菜单
        if self.get_app(request, True):
            return super(WeChatAdmin, self).get_model_perms(request)
        return {}

    def check_wechat_permission(self, request, operate="", category="", obj=None):
        if not self.has_wechat_permission(request, operate, category, obj):
            raise PermissionDenied

    def has_wechat_permission(self, request, operate="", category="", obj=None):
        app = self.get_app(request)
        category = category or self.__category__
        return has_wechat_permission(request, app, category, operate, obj)

    def has_add_permission(self, request):
        return self.has_wechat_permission(request, "add")

    def has_change_permission(self, request, obj=None):
        return self.has_wechat_permission(request, "change", obj=obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_wechat_permission(request, "delete", obj=obj)

    def get_app(self, request, nullable=False):
        if not hasattr(request, "app"):
            app_id = self._get_request_params(request, "app_id")
            try:
                request.app = WeChatApp.objects.get_by_id(app_id)
            except WeChatApp.DoesNotExist:
                if not nullable:
                    raise
                request.app = None
        return request.app

    @staticmethod
    def _get_request_params(request, param):
        if not hasattr(request, param):
            preserved_filters_str = request.GET.get('_changelist_filters')
            if preserved_filters_str:
                preserved_filters = dict(parse_qsl(preserved_filters_str))
            else:
                preserved_filters = dict()
            value = (request.GET.get(param)
                or preserved_filters.get(param)
                or request.resolver_match.kwargs.get(param))
            setattr(request, param, value)
        return getattr(request, param)

    def logger(self, request):
        app = self.get_app(request)
        name = "wechat.admin.{0}".format(app.name)
        return logging.getLogger(name)


class DynamicChoiceForm(forms.ModelForm):
    content_field = "_content"
    type_field = "type"
    origin_fields = tuple()

    def __init__(self, *args, **kwargs):
        inst = kwargs.get("instance")
        if inst:
            initial = kwargs.get("initial", {})
            initial.update(getattr(inst, self.content_field))
            kwargs["initial"] = initial
        super(DynamicChoiceForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(DynamicChoiceForm, self).clean()
        if self.type_field not in cleaned_data:
            self.add_error(self.type_field, "")
            return
        type = cleaned_data[self.type_field]
        fields = self.allowed_fields(type, cleaned_data)

        content = dict()
        for k in set(cleaned_data.keys()).difference(self.origin_fields):
            if k in fields:
                content[k] = cleaned_data[k]
                del cleaned_data[k]
        cleaned_data[self.content_field] = content
        return cleaned_data

    def allowed_fields(self, type, cleaned_data):
        raise NotImplementedError()

    def save(self, commit=True, *args, **kwargs):
        model = super(DynamicChoiceForm, self).save(False, *args, **kwargs)
        setattr(model, self.content_field,
            self.cleaned_data[self.content_field])
        if commit:
            model.save()
        return model


def patch_admin(admin):
    """
    :type admin: django.contrib.admin.sites.AdminSite
    """
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
            # 首页 追加app列表
            app_dict = _build_wechat_app_dict(self, request)
            if app_dict["has_module_perms"]:
                rv[fake_app_label] = app_dict
        elif not rv:
            pass
        elif label == app_label:
            app_id = request.resolver_match.kwargs.get("app_id")
            if app_id:
                # 各公众号管理菜单
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
                # 原始菜单
                pass

        return rv

    def _build_wechat_app_dict(self, request):
        if request.user.is_superuser:
            apps = WeChatApp.objects.all()
        else:
            perms = get_user_permissions(request.user)
            allowed_apps = {
                k for k, ps in perms.items() if ps != {"manage"}
            }
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
            'name': _(app_label),
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


def register_admins(site):
    """将admin注册到site中"""
    from .wechatapp import WeChatAppAdmin
    site.register(WeChatApp, WeChatAppAdmin)
    for admin in registered_admins:
        site.register(admin.model, admin)


def register_admin(model):
    """注册admin 为后续注册到site中做准备"""
    def decorator(cls):
        cls.model = model
        return cls
    return decorator
