from urllib.parse import parse_qsl

from django import forms
from django.contrib import admin
from django.utils.encoding import force_text
from django.utils.translation import gettext_lazy as _

from ..models import WeChatApp

def _endswith_appid(d):
    for k in d:
        if k.endswith("__app_id"):
            return d[k]

class WeChatAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        request.GET._mutable = True
        self._app_id = request.GET.get("app_id")
        request.GET.pop("app_id", None)
        request.GET._mutable = False

        post = request.POST.copy()
        if admin.helpers.ACTION_CHECKBOX_NAME not in post:
            post.update({admin.helpers.ACTION_CHECKBOX_NAME: None})
            request._set_post(post)
        extra_context = self._update_context(request, extra_context)
        return super().changelist_view(request, extra_context)

    def render_change_form(self, request, context, *args, **kwargs):
        context = self._update_context(request, context)
        return super().render_change_form(request, context, *args, **kwargs)

    def _update_context(self, request, context):
        app_id = self.get_request_app_id(request)
        context = context or dict()
        context.update(dict(
            app_id=app_id,
            app=WeChatApp.get_by_id(app_id)
        ))
        return context

    def get_queryset(self, request):
        rv = super().get_queryset(request)
        # TODO: 检查权限
        app_id = self.get_request_app_id(request)
        return self._filter_app_id(rv, app_id) if app_id else rv.none()

    def _filter_app_id(self, queryset, app_id):
        return queryset.filter(app_id=app_id)
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.app_id = self.get_request_app_id(request)
        # TODO: 没有app_id 应该404
        # TODO: 检查权限
        return super().save_model(request, obj, form, change)

    def get_model_perms(self, request):
        # 隐藏首页上的菜单
        if self.get_request_app_id(request):
            return super().get_model_perms(request)
        return {}

    _app_id = None
    def get_request_app_id(self, request):
        if not self._app_id:
            preserved_filters_str = request.GET.get('_changelist_filters')
            if preserved_filters_str:
                preserved_filters = dict(parse_qsl(preserved_filters_str))
            else:
                preserved_filters = dict()
            self._app_id = (request.GET.get("app_id") 
                or preserved_filters.get("app_id") 
                or request.resolver_match.kwargs.get("app_id"))
        return self._app_id

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