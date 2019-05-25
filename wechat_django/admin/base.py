# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import django
from django import forms
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.contrib.admin.views.main import ChangeList
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from object_tool import CustomObjectToolModelAdminMixin
import six
from wechatpy.exceptions import WeChatClientException

from ..models.permission import get_user_permissions


registered_admins = []


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
            resp = delete_selected(self, request, queryset)
            resp.context_data.update(
                wechat_app=request.app,
                wechat_app_id=request.app_id
            )
            return resp

        with transaction.atomic():
            for o in queryset.all():
                try:
                    if not self.has_delete_permission(request, o):
                        raise PermissionDenied
                    o.delete()
                except WeChatClientException:
                    msg = _("delete %(category)s failed: %(obj)s") % dict(
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


class WeChatChangeList(ChangeList):
    def __init__(self, request, *args, **kwargs):
        super(WeChatChangeList, self).__init__(request, *args, **kwargs)
        self.request = request

    def url_for_result(self, result):
        view = "admin:%s_%s_change" % (
            self.opts.app_label, self.opts.model_name)
        kwargs = dict(
            object_id=getattr(result, self.pk_attname),
            wechat_app_id=self.request.app_id
        )
        return reverse(
            view, kwargs=kwargs, current_app=self.model_admin.admin_site.name)


class WeChatModelAdminMetaClass(forms.MediaDefiningClass):
    def __new__(cls, name, bases, attrs):
        model = attrs.pop("__model__", None)
        self = super(WeChatModelAdminMetaClass, cls).__new__(
            cls, name, bases, attrs)
        if name != "WeChatModelAdmin" and model:
            registered_admins.append((model, self))
        return self


class WeChatModelAdmin(six.with_metaclass(WeChatModelAdminMetaClass, CustomObjectToolModelAdminMixin, admin.ModelAdmin)):
    """所有微信相关业务admin的基类

    并且通过request.app_id及request.app拿到app信息
    """
    change_form_template = "admin/wechat_django/change_form.html"
    change_list_template = "admin/wechat_django/change_list.html"
    objecttool_form_template = "admin/wechat_django/objecttool_form.html"

    #region view
    def get_changelist(self, request):
        return WeChatChangeList

    def get_urls(self):
        urlpatterns = super(WeChatModelAdmin, self).get_urls()
        # django 1.11 替换urlpattern为命名式的
        if django.VERSION[0] < 2:
            for pattern in urlpatterns:
                pattern._regex = pattern._regex.replace(
                    "(.+)", "(?P<object_id>.+)")
        return urlpatterns

    def _clientaction(self, request, action, failed_msg, kwargs=None):
        kwargs = kwargs or dict()
        try:
            msg = action()
            self.message_user(request, msg)
        except Exception as e:
            kwargs.update(exc=e)
            msg = failed_msg % kwargs
            if isinstance(e, WeChatClientException):
                self.logger(request).warning(msg, exc_info=True)
            else:
                self.logger(request).error(msg, exc_info=True)
            self.message_user(request, msg, level=messages.ERROR)
    #endregion

    #region model
    def get_queryset(self, request):
        return (super(WeChatModelAdmin, self)
            .get_queryset(request).filter(app_id=request.app_id))

    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = request.app_id
        return super(WeChatModelAdmin, self).save_model(
            request, obj, form, change)
    #endregion

    #region permissions
    def check_wechat_permission(self, request, operate="", category="", obj=None):
        if not self.has_wechat_permission(request, operate, category, obj):
            raise PermissionDenied

    def has_wechat_permission(self, request, operate="", category="", obj=None):
        if not hasattr(request, "app"):
            return False
        app = request.app
        category = category or self.__category__
        return has_wechat_permission(request, app, category, operate, obj)

    def has_add_permission(self, request):
        return self.has_wechat_permission(request, "add")

    def has_change_permission(self, request, obj=None):
        return self.has_wechat_permission(request, "change", obj=obj)

    def has_delete_permission(self, request, obj=None):
        return self.has_wechat_permission(request, "delete", obj=obj)

    def has_module_permission(self, request):
        """是否拥有任意本公众号管理权限"""
        if not hasattr(request, "app"):
            return False
        return bool(get_user_permissions(request.user, request.app))
    #endregion

    #region utils
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
