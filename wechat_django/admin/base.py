# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django import forms
from django.contrib import admin
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.templatetags import admin_list
from django.contrib.admin.views.main import ChangeList as _ChangeList
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
import six
from wechatpy.exceptions import WeChatClientException

from ..models.permission import get_user_permissions
from ..utils.web import mutable_GET


registered_admins = []


@admin_list.register.inclusion_tag('admin/wechat_django/search_form.html')
def search_form(cl):
    """
    搜索form带app_id
    """
    return admin_list.search_form(cl)


class RecursiveDeleteActionMixin(object):
    """逐一删除混合类"""
    def get_actions(self, request):
        actions = super(RecursiveDeleteActionMixin, self).get_actions(request)
        if "delete_selected" in actions:
            actions["delete_selected"] = (
                RecursiveDeleteActionMixin.delete_selected_recusively,
                actions["delete_selected"][1],
                actions["delete_selected"][2]
            )
        return actions

    def delete_selected_recusively(self, request, queryset):
        """逐一删除"""
        if not request.POST.get("post"):
            return delete_selected(self, request, queryset)

        with transaction.atomic():
            for o in queryset.all():
                try:
                    if not self.has_delete_permission(request, o):
                        raise PermissionDenied
                    o.delete()
                except WeChatClientException:
                    msg = _("delete %(category) failed: %(obj)s") % dict(
                        category=self.model.verbose_name_plural,
                        obj=o
                    )
                    self.logger(request).warning(msg, exc_info=True)
                    raise
    delete_selected.short_description = _("delete selected")


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


class WeChatModelAdminMetaClass(forms.MediaDefiningClass):
    def __new__(cls, name, bases, attrs):
        model = attrs.pop("__model__", None)
        self = super(WeChatModelAdminMetaClass, cls).__new__(
            cls, name, bases, attrs)
        if name != "WeChatModelAdmin" and model:
            registered_admins.append((model, self))
        return self

    # def __init__(cls, name, bases, attrs):
    #     # 对默认视图加装admin_view装饰器
    #     if name == "WeChatModelAdmin":
    #         views = (
    #             "changelist_view", "add_view", "history_view", "delete_view",
    #             "change_view")
    #         for view in views:
    #             view_func = getattr(cls, view)
    #             setattr(cls, view, admin_view(view_func))

    #     super(WeChatModelAdminMetaClass, cls).__init__(
    #         name, bases, attrs)


class WeChatModelAdmin(six.with_metaclass(WeChatModelAdminMetaClass, admin.ModelAdmin)):
    """所有微信相关业务admin的基类

    可以通过self.request拿到request对象
    并且通过request.app_id及request.app拿到app信息
    """
    #region view
    def changelist_view(self, request, extra_context=None):
        # 允许没有选中的actions
        post = request.POST.copy()
        if admin.helpers.ACTION_CHECKBOX_NAME not in post:
            post.update({admin.helpers.ACTION_CHECKBOX_NAME: None})
            request._set_post(post)
        return super(WeChatModelAdmin, self).changelist_view(request, extra_context)

    def changeform_view(self, request, object_id=None, form_url="", *args, **kwargs):
        if object_id and not request.app_id:
            # 对于没有app_id的请求,重定向至有app_id的地址
            obj = self.model.objects.get(pk=object_id)
            app_id = getattr(obj, "app_id", obj.app.id)
            return redirect(request.path + "?" + urlencode(dict(
                _changelist_filters="app_id=" + str(app_id)
            )), permanent=True)
        form_url = form_url or "?{0}".format(request.GET.urlencode())
        return super(WeChatModelAdmin, self).changeform_view(
            request, object_id, form_url, *args, **kwargs)

    def get_changelist(self, request, **kwargs):
        return ChangeList

    def get_preserved_filters(self, request):
        with mutable_GET(request) as GET:
            GET["app_id"] = str(self.request.app_id)
            try:
                return super(WeChatModelAdmin, self).get_preserved_filters(request)
            finally:
                GET.pop("app_id", None)
    #endregion

    #region model
    def get_queryset(self, request):
        rv = super(WeChatModelAdmin, self).get_queryset(request)
        app_id = request.app_id
        return self._filter_app_id(rv, app_id) if app_id else rv.none()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = request.app_id
        return super(WeChatModelAdmin, self).save_model(request, obj, form, change)
    #endregion

    #region permissions
    def get_model_perms(self, request):
        # 隐藏首页上的菜单
        if getattr(request, "app_id", None):
            return super(WeChatModelAdmin, self).get_model_perms(request)
        return {}

    def check_wechat_permission(self, request, operate="", category="", obj=None):
        if not self.has_wechat_permission(request, operate, category, obj):
            raise PermissionDenied

    def has_wechat_permission(self, request, operate="", category="", obj=None):
        app = request.app
        category = category or self.__category__
        return has_wechat_permission(request, app, category, operate, obj)

    def has_add_permission(self, request):
        return self.has_wechat_permission(request, "add")

    def has_change_permission(self, request, obj=None):
        return self.has_wechat_permission(request, "change", obj=obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_wechat_permission(request, "delete", obj=obj)
    #endregion

    #region utils
    def _filter_app_id(self, queryset, app_id):
        return queryset.filter(app_id=app_id)

    def logger(self, request):
        name = "wechat.admin.{0}".format(request.app.name)
        return logging.getLogger(name)
    #endregion


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
