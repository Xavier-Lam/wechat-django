# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import appmethod, WeChatModel
from .base import WeChatTestCase


class ModelBaseTestCase(WeChatTestCase):
    def test_appmethod(self):
        """测试appmethod"""
        class DebugModel(WeChatModel):
            class Meta(object):
                abstract = True

            @classmethod
            @appmethod
            def test(cls, app, *args, **kwargs):
                return cls, app, args, kwargs

            @classmethod
            @appmethod("another")
            def test1(cls, app, *args, **kwargs):
                return cls, app, args, kwargs

        def assertAppMethodEqual(func, app, funcname):
            args = (1, 2)
            kwargs = dict(a=1, b=2)
            cls, app_, args_, kwargs_ = func(*args, **kwargs)
            self.assertEqual(cls, DebugModel)
            self.assertEqual(app_, app)
            self.assertEqual(args_, args)
            self.assertEqual(kwargs_, kwargs)
            self.assertEqual(func.__name__, funcname)
            self.assertEqual(
                func.__qualname__, "{0}.{1}".format("WeChatApp", funcname))

        assertAppMethodEqual(self.app.test, self.app, "test")
        assertAppMethodEqual(self.app.another, self.app, "another")
        assertAppMethodEqual(self.another_app.test, self.another_app, "test")
        assertAppMethodEqual(
            self.another_app.another, self.another_app, "another")
