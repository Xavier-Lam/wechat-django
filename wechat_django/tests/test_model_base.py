# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..models import PublicApp, WeChatApp
from ..models.base import WeChatModel
from .base import WeChatTestCase


class ModelBaseTestCase(WeChatTestCase):
    def test_shortcut(self):
        """测试shortcut"""
        class DebugModel(WeChatModel):
            class Meta(object):
                abstract = True

            @WeChatApp.shortcut
            def test(cls, app, *args, **kwargs):
                return cls, app, args, kwargs

            @WeChatApp.shortcut("another")
            def test1(cls, app, *args, **kwargs):
                return cls, app, args, kwargs

            @PublicApp.shortcut
            def public_only(cls, app, *args, **kwargs):
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
        self.assertTrue(hasattr(PublicApp, "public_only"))
        self.assertFalse(hasattr(WeChatApp, "public_only"))

    def test_related_manager(self):
        app_type = type(self.app)
        self.assertEqual(self.app.users.app, self.app)
        self.assertIsInstance(self.app.users.app, app_type)
        self.assertEqual(self.app.users.all().app, self.app)
        self.assertIsInstance(self.app.users.all().app, app_type)
        self.assertEqual(self.app.materials.app, self.app)
        self.assertIsInstance(self.app.materials.app, app_type)
        self.assertEqual(self.app.materials.all().app, self.app)
        self.assertIsInstance(self.app.materials.all().app, app_type)
        self.assertEqual(self.app.templates.app, self.app)
        self.assertIsInstance(self.app.templates.app, app_type)
        self.assertEqual(self.app.templates.all().app, self.app)
        self.assertIsInstance(self.app.templates.app, app_type)
