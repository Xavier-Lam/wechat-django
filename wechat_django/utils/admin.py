# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _


def linkify(field_name):
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
        link_url = reverse(view_name, args=[linked_obj.id])
        link_url += "?app_id={0}".format(obj.app.id)
        return '<a href="{0}">{1}</a>'.format(link_url, linked_obj)

    _linkify.short_description = _(field_name)
    _linkify.allow_tags = True
    _linkify.admin_order_field = field_name
    return _linkify


def enum2choices(enum):
    pattern = re.compile(r"^[A-Z][A-Z_\d]+$")
    return tuple(
        (getattr(enum, key), _(key))
        for key in dir(enum)
        if re.match(pattern, key)
    )
