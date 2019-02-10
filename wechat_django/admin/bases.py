from contextlib import contextmanager
import logging

from django import forms
from django.contrib import admin
from django.contrib.admin.templatetags import admin_list
from django.contrib.admin.views.main import ChangeList as _ChangeList
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.utils.encoding import force_text
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from six.moves.urllib.parse import parse_qsl

from ..models import WeChatApp, WECHATPERM_PREFIX

@contextmanager
def mutable_GET(request):
    request.GET._mutable = True
    try:
        yield request.GET
    finally:
        request.GET._mutable = False

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
    strings = (app.name, category, operate)
    perms = []
    for i in range(len(list(filter(bool, strings)))):
        perm = "_".join(strings[: i + 1])
        perms.append("{label}.{prefix}{perm}".format(
            label="wechat_django",
            prefix=WECHATPERM_PREFIX,
            perm=perm
        ))
    
    for perm in perms:
        if request.user.has_perm(perm, None):
            return True

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

class WeChatAdmin(admin.ModelAdmin):
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
        return super(WeChatAdmin, self).history_view(request, object_id, 
            extra_context)

    def delete_view(self, request, object_id, extra_context=None):
        extra_context = self._update_context(request, extra_context)
        return super(WeChatAdmin, self).delete_view(request, object_id, 
            extra_context)

    def changeform_view(self, request, object_id=None, form_url="", 
        extra_context=None):
        if object_id and not self.get_app(request, True):
            # 对于没有app_id的请求,重定向至有app_id的地址
            obj = self.model.objects.get(id=object_id)
            app_id = getattr(obj, "app_id", obj.app.id)
            return redirect(request.path + "?" + urlencode(dict(
                _changelist_filters="app_id=" + str(app_id)
            )), permanent=True)
        return super(WeChatAdmin, self).changeform_view(request, object_id,
            form_url, extra_context)

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
                request.app = WeChatApp.get_by_id(app_id)
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
    content_field = ""
    type_field = ""
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