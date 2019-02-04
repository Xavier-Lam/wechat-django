from contextlib import contextmanager
import logging

from django import forms
from django.contrib import admin
from django.contrib.admin.templatetags import admin_list
from django.contrib.admin.views.main import ChangeList as _ChangeList
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _
from six.moves.urllib.parse import parse_qsl

from ..models import WeChatApp

@contextmanager
def mutable_GET(GET):
    GET._mutable = True
    try:
        yield GET
    finally:
        GET._mutable = False

@admin_list.register.inclusion_tag('admin/wechat_django/search_form.html')
def search_form(cl):
    """
    搜索form带app_id
    """
    return admin_list.search_form(cl)

class ChangeList(_ChangeList):
    def __init__(self, request, *args, **kwargs):
        # app_id在changelist中会抛出IncorrectLookupParameters异常
        self.app_id = request.GET.get("app_id")
        with mutable_GET(request.GET) as GET:
            GET.pop("app_id", None)

        super().__init__(request, *args, **kwargs)

        with mutable_GET(request.GET) as GET:
            GET["app_id"] = self.app_id

    def get_query_string(self, new_params=None, remove=None):
        # filter的链接会掉querystring
        query = super().get_query_string(new_params, remove).replace("?", "&")
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
        return super().changelist_view(request, extra_context)

    def render_change_form(self, request, context, *args, **kwargs):
        context = self._update_context(request, context)
        return super().render_change_form(request, context, *args, **kwargs)

    def get_changelist(self, request, **kwargs):
        return ChangeList

    def _update_context(self, request, context):
        app_id = self.get_request_app_id(request)
        context = context or dict()
        context.update(dict(
            app_id=app_id,
            app=WeChatApp.get_by_id(app_id)
        ))
        return context

    def get_queryset(self, request):
        self.request = request
        rv = super().get_queryset(request)
        # TODO: 检查权限
        app_id = self.get_request_app_id(request)
        return self._filter_app_id(rv, app_id) if app_id else rv.none()

    def get_preserved_filters(self, request):
        with mutable_GET(request.GET) as GET:
            GET["app_id"] = self.get_request_app_id(request)
            try:
                return super().get_preserved_filters(request)
            finally:
                GET.pop("app_id", None)

    def _filter_app_id(self, queryset, app_id):
        return queryset.filter(app_id=app_id)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = self.get_request_app_id(request)
        return super().save_model(request, obj, form, change)

    def get_model_perms(self, request):
        # 隐藏首页上的菜单
        if self.get_request_app_id(request):
            return super().get_model_perms(request)
        return {}

    def get_request_app_id(self, request):
        return self._get_request_params(request, "app_id")
    
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
        app = WeChatApp.get_by_id(self.get_request_app_id(request))
        name = "wechat.admin.{0}".format(app.name)
        return logging.getLogger(name)

class DynamicChoiceForm(forms.ModelForm):
    content_field = ""
    type_field = ""
    origin_fields = tuple()

    def __init__(self, *args, **kwargs):
        inst = kwargs.get("instance")
        if inst:
            type = getattr(inst, self.type_field)
            initial = kwargs.get("initial", {})
            initial.update(getattr(inst, self.content_field))
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
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
        model = super().save(False, *args, **kwargs)
        setattr(model, self.content_field, 
            self.cleaned_data[self.content_field])
        if commit:
            model.save()
        return model