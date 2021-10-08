from django.core.cache import cache
from django.core.cache.backends.base import BaseCache
from django import forms

from .django import decriptor2contributor


class ModelFieldMixin:
    """Mock django's model field"""

    def __init__(self, verbose_name=None, **kwargs):
        self.verbose_name = verbose_name
        self.default = kwargs.pop("default", None)
        self.null = kwargs.pop("null", True)
        self.help_text = kwargs.pop("help_text", None)
        self.choices = kwargs.pop("choices", None)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        defaults = {
            "required": not self.null,
            "label": self.verbose_name,
            "help_text": self.help_text,
            "initial": self.default
        }
        defaults.update(kwargs)
        if form_class is None:
            form_class = forms.CharField
        if self.choices is not None:
            defaults['choices'] = self.choices
            if self.null:
                defaults['empty_value'] = None
            if choices_form_class is not None:
                form_class = choices_form_class
            else:
                form_class = forms.TypedChoiceField
        return form_class(**defaults)

    def get_default(self):
        if callable(self.default):
            return self.default()
        return self.default


class CacheFieldDescriptor(ModelFieldMixin):
    def __init__(self, verbose_name=None, *, expires_in=None, **kwargs):
        self.expires_in = expires_in
        super().__init__(verbose_name, **kwargs)

    def __get__(self, obj, objtype):
        return self.get_cache(obj).get(self.get_key(obj), self.default)

    def __set__(self, obj, value):
        self.get_cache(obj).set(
            self.get_key(obj),
            value,
            self.expires_in
        )

    def __delete__(self, obj):
        self.get_cache(obj).delete(self.get_key(obj))

    def __set_name__(self, owner, name):
        self._owner = owner
        self.name = name

    def get_key(self, obj):
        # TODO: 确保pk存在方可调用
        return "cachefield:{label}:{model}:{pk}:{key}".format(
            label=self._owner._meta.app_label,
            model=self._owner._meta.model_name,
            pk=obj.pk,
            key=self.name
        )

    def get_cache(self, obj) -> BaseCache:
        return cache


class ModelPropertyDescriptor(ModelFieldMixin):
    def __init__(self, verbose_name=None, *, type=str, auto_commit=False,
                 target=None, **kwargs):
        self.type = type
        self.auto_commit = auto_commit
        if target:
            self.target = target
        super().__init__(verbose_name, **kwargs)

    def __get__(self, obj, objtype):
        storage = self.get_storage(obj)
        if self.null or self.default is not None:
            return storage.get(self.name, self.default)
        else:
            return storage[self.name]

    def __set__(self, obj, value):
        storage = self.get_storage(obj)
        storage[self.name] = value
        self.auto_commit and obj.save()

    def __delete__(self, obj):
        storage = self.get_storage(obj)
        del storage[self.name]
        self.auto_commit and obj.save()

    def __set_name__(self, owner, name):
        self.name = name

    def get_storage(self, obj) -> dict:
        return getattr(obj, self.target)


class FieldAliasDescriptor(ModelFieldMixin):
    admin_order_field = None

    def __init__(self, alias, verbose_name=None, **kwargs):
        self.alias = alias
        self.admin_order_field = alias
        super().__init__(verbose_name, **kwargs)

    def __get__(self, obj, objtype):
        return getattr(obj, self.alias)

    def __set__(self, obj, value):
        setattr(obj, self.alias, value)

    def __delete__(self, obj):
        delattr(obj, self.alias)

    def __set_name__(self, owner, name):
        self.name = name


CacheField = decriptor2contributor(CacheFieldDescriptor)
ModelProperty = decriptor2contributor(ModelPropertyDescriptor)
FieldAlias = decriptor2contributor(FieldAliasDescriptor)
