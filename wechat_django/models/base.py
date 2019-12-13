# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import update_wrapper, wraps

from django.db import models as m
from django.db.models.manager import BaseManager
from django.utils.encoding import force_bytes
import six


class ShortcutMethod(classmethod):
    def __init__(self, cls, method_name, func):
        self.cls = cls
        self.method_name = method_name
        self.func = func
        super(ShortcutMethod, self).__init__(func)

    def bind(self, cls):
        func = self.func
        method_name = self.method_name
        shortcut = wraps(func)(lambda *args, **kw: func(cls, *args, **kw))
        shortcut.__name__ = method_name
        shortcut.__qualname__ = "{0}.{1}".format(self.cls.__name__,
                                                 method_name)
        setattr(self.cls, method_name, shortcut)


class ShortcutBound(object):
    _registered_models = dict()

    @classmethod
    def shortcut(cls, func_or_name):
        """可以把其他对象的方法注册到本对象的语法糖

            class SomeModel(WeChatModel):
                @WeChatApp.shortcut
                def awesome_method(cls, app, *args, **kwargs):
                    # ...

                @WeChatApp.shortcut("another_method")
                def method(cls, app, *args, **kwargs):
                    # ...

            res = SomeModel.awesome_method(app, *args, **kwargs)
            res = app.awesome_method(*args, **kwargs)
            res = app.another_method(*args, **kwargs)
        """

        def shortcuted(func):
            return ShortcutMethod(cls, method_name, func)

        if callable(func_or_name):
            method_name = func_or_name.__name__
            return shortcuted(func_or_name)
        else:
            method_name = str(func_or_name)
            return shortcuted

    @classmethod
    def register_model(cls, model_cls):
        """将某个WeChatModel注册为某种WeChatApp的专有model"""
        # 获取WeChatModel的基类
        base_cls = model_cls.get_base_cls()

        if cls not in cls._registered_models:
            cls._registered_models[cls] = dict()

        cls._registered_models[cls][base_cls] = model_cls
        return model_cls

    @classmethod
    def get_registered_model(cls, base_cls):
        """获取本类型app某一关联WeChatModel类型"""
        for class_ in cls.mro():
            if class_ is m.Model:
                raise KeyError(cls, base_cls)
            if base_cls in cls._registered_models.get(class_, []):
                return cls._registered_models[class_][base_cls]


class WeChatQuerySet(m.QuerySet):
    @property
    def app(self):
        # TODO: 可能存在related非app的情况
        return self._hints.get("instance")


class WeChatManager(BaseManager.from_queryset(WeChatQuerySet)):
    @property
    def app(self):
        # TODO: 可能存在core_filters不存在的情况,即不是related_manager
        return self.core_filters["app"]


class WeChatModelMetaClass(m.base.ModelBase):
    def __new__(meta, name, bases, attrs):
        # python2.7 __str__必须返回bytestring
        if six.PY2 and "__str__" in attrs:
            __str__ = attrs.pop("__str__")
            attrs["__str__"] = update_wrapper(
                lambda self: force_bytes(__str__(self)), __str__)

        cls = super(WeChatModelMetaClass, meta).__new__(meta, name, bases,
                                                        attrs)

        for attr, val in attrs.items():
            # 将modelmethod转换为shortcut method
            isinstance(val, ShortcutMethod) and val.bind(cls)

        return cls


class WeChatFixTypeIterable(m.query.ModelIterable):
    """根据不同类型的WeChatApp,生成不同类型的WeChatModel实例"""

    def __iter__(self):
        for obj in super(WeChatFixTypeIterable, self).__iter__():
            obj.fix_type()
            yield obj


class WeChatFixTypeQuerySet(WeChatQuerySet):
    """自动修正类型的QuerySet"""

    def create(self, **kwargs):
        obj = super(WeChatFixTypeQuerySet, self).create(**kwargs)
        obj.fix_type()
        return obj


class WeChatFixTypeManager(WeChatManager.from_queryset(WeChatFixTypeQuerySet)):  # noqa
    """自动修正类型的Manager"""

    def get_queryset(self):
        queryset = super(WeChatFixTypeManager, self).get_queryset()
        queryset = queryset.select_related("app")
        queryset._iterable_class = WeChatFixTypeIterable
        return queryset


class WeChatModel(six.with_metaclass(WeChatModelMetaClass, m.Model)):
    objects = WeChatManager()

    def fix_type(self):
        """修正model的类型"""
        base_cls = type(self).get_base_cls()
        self.__class__ = type(self.app).get_registered_model(base_cls)

    @classmethod
    def get_base_cls(cls):
        """获取WeChatModel代理Model的基类"""
        mro = cls.mro()
        return mro[mro.index(WeChatModel) - 1]

    class Meta(object):
        abstract = True
