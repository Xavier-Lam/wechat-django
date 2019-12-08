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


class WeChatQuerySet(m.QuerySet):
    @property
    def app(self):
        return self._hints.get("instance")


class WeChatManager(BaseManager.from_queryset(WeChatQuerySet)):
    @property
    def app(self):
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


class WeChatModel(six.with_metaclass(WeChatModelMetaClass, m.Model)):
    objects = WeChatManager()

    class Meta(object):
        abstract = True
