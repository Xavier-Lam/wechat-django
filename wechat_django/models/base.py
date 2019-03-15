# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import wraps

from django.db import models as m
from django.utils.decorators import available_attrs
import six

from . import WeChatApp


def appmethod(func_or_name):
    """可以把方法注册到WeChatApp上的语法糖
    
        class SomeModel(WeChatModel):
            @classmethod
            @appmethod
            def awesome_method(cls, app, *args, **kwargs):
                # ...

            @classmethod
            @appmethod("another_method")
            def method(cls, app, *args, **kwargs):
                # ...
        
        res = SomeModel.awesome_method(app, *args, **kwargs)
        res = app.awesome_method(*args, **kwargs)
        res = app.another_method(*args, **kwargs)
    """    
    def decorator(func):
        # 防止副作用
        def wrapped_func(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped_func._appmethod = name

        return wraps(func, assigned=available_attrs(func))(wrapped_func)

    if callable(func_or_name):
        name = func_or_name.__name__
        return decorator(func_or_name)
    else:
        name = func_or_name
        return decorator


class WeChatModelMetaClass(m.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        self = super(WeChatModelMetaClass, cls).__new__(
            cls, name, bases, attrs)

        for attr in attrs:
            # 将modelmethod转换为appmethod
            value = getattr(self, attr)
            if getattr(value, "_appmethod", False):
                method = value
                def wrapped_func(self, *args, **kwargs):
                    return method(self, *args, **kwargs)

                setattr(
                    WeChatApp, method._appmethod,
                    wraps(method)(wrapped_func))

        return self


class WeChatModel(six.with_metaclass(WeChatModelMetaClass, m.Model)):
    class Meta(object):
        abstract = True
