# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from six.moves import reduce
from six.moves.urllib.parse import parse_qsl


def anchor(text, href, **kwargs):
    """转化为a标签"""
    @mark_safe
    def wrapper(modeladmin, obj):
        kwargs.update(
            href=href,
            text=text
        )
        for key, value in kwargs.items():
            if callable(value):
                kwargs[key] = value(modeladmin, obj)
        return kwargs["text"] and '<a href="{href}">{text}</a>'.format(**kwargs)
    return wrapper


def foreignkey(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    @mark_safe
    def _linkify(obj):
        app_label = obj._meta.app_label
        linked_obj = getattr(obj, field_name)
        model_name = linked_obj._meta.model_name
        view_name = "admin:{app_label}_{model_name}_change".format(
            app_label=app_label,
            model_name=model_name
        )
        link_url = reverse(view_name, kwargs=dict(
            object_id=linked_obj.id,
            wechat_app_id=obj.app_id
        ))
        return '<a href="{0}">{1}</a>'.format(link_url, linked_obj)

    _linkify.short_description = _(field_name)
    _linkify.admin_order_field = field_name
    return _linkify


def list_property(field_name, **kwargs):
    def _from_property(obj):
        rv = reduce(getattr, field_name.split("."), obj)
        return rv() if callable(rv) else rv

    for key, value in kwargs.items():
        setattr(_from_property, key, value)
    return _from_property


def field_property(field_name, **kwargs):
    def _from_property(admin, obj=None):
        if not obj:
            return None
        rv = reduce(getattr, field_name.split("."), obj)
        return rv() if callable(rv) else rv

    for key, value in kwargs.items():
        setattr(_from_property, key, value)
    return _from_property


def get_request_params(request, param):
    """从请求信息中获取想要的信息"""
    if not hasattr(request, param):
        preserved_filters_str = request.GET.get('_changelist_filters')
        if preserved_filters_str:
            preserved_filters = dict(parse_qsl(preserved_filters_str))
        else:
            preserved_filters = dict()
        value = (request.GET.get(param)
            or preserved_filters.get(param))
        setattr(request, param, value)
    return getattr(request, param)
