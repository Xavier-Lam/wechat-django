import time

from django.core.cache import cache
from django.test import TestCase
from django_fake_model import models as f
from jsonfield import JSONField

from wechat_django.utils.model import CacheField, FieldAlias, ModelProperty


DEFAULT = "default"
VALUE = "value"


class DummyUtilTestCaseModel(f.FakeModel):
    storage = JSONField(default={})

    nullable = ModelProperty(null=True, target="storage")
    default = ModelProperty(default=DEFAULT, null=False, target="storage")
    required = ModelProperty(null=False, target="storage")
    auto_commit = ModelProperty(auto_commit=True, target="storage")

    c = CacheField(expires_in=5)

    alias = FieldAlias("nullable")


@DummyUtilTestCaseModel.fake_me
class UtilModelTestCase(TestCase):
    def test_model_property(self):
        """测试JsonField衍生出的property"""
        model = DummyUtilTestCaseModel.objects.create()

        self.assertIsNone(model.nullable)
        self.assertEqual(model.default, DEFAULT)
        self.assertRaises(KeyError, lambda: model.required)

        model.nullable = VALUE
        model.default = VALUE
        model.required = VALUE
        self.assertEqual(model.nullable, VALUE)
        self.assertEqual(model.default, VALUE)
        self.assertEqual(model.required, VALUE)
        self.assertEqual(model.storage["nullable"], VALUE)
        self.assertEqual(model.storage["default"], VALUE)
        self.assertEqual(model.storage["required"], VALUE)

        del model.nullable
        del model.default
        del model.required
        self.assertIsNone(model.nullable)
        self.assertEqual(model.default, DEFAULT)
        self.assertRaises(KeyError, lambda: model.required)
        self.assertNotIn("nullable", model.storage)
        self.assertNotIn("default", model.storage)
        self.assertNotIn("required", model.storage)

        # 测试自动保存
        model.nullable = VALUE
        model = DummyUtilTestCaseModel.objects.get(pk=model.pk)
        self.assertNotEqual(model.nullable, VALUE)
        model.auto_commit = VALUE
        model = DummyUtilTestCaseModel.objects.get(pk=model.pk)
        self.assertEqual(model.auto_commit, VALUE)
        self.assertEqual(model.storage["auto_commit"], VALUE)
        del model.auto_commit
        model = DummyUtilTestCaseModel.objects.get(pk=model.pk)
        self.assertIsNone(model.auto_commit)
        self.assertNotIn("auto_commit", model.storage)

    def test_cache_field(self):
        """测试CacheField"""
        model = DummyUtilTestCaseModel.objects.create()
        key = "cachefield:{label}:{model}:{pk}:{key}".format(
            label=model._meta.app_label,
            model=model._meta.model_name,
            pk=model.pk,
            key="c"
        )

        self.assertIsNone(model.c)
        model.c = DEFAULT
        self.assertEqual(model.c, DEFAULT)
        model = DummyUtilTestCaseModel.objects.get(pk=model.pk)
        self.assertEqual(model.c, DEFAULT)
        self.assertEqual(cache.get(key), DEFAULT)

        model.c = VALUE
        self.assertEqual(model.c, VALUE)
        model = DummyUtilTestCaseModel.objects.get(pk=model.pk)
        self.assertEqual(model.c, VALUE)
        self.assertEqual(cache.get(key), VALUE)
        raw_key = cache.make_key(key)
        self.assertAlmostEqual(cache._expire_info.get(raw_key),
                               time.time() + 5, delta=0.1)

        del model.c
        self.assertIsNone(model.c)
        model = DummyUtilTestCaseModel.objects.get(pk=model.pk)
        self.assertIsNone(model.c)
        self.assertIsNone(cache.get(key))

    def test_field_alias(self):
        """测试FieldAlias"""
        self.assertEqual(DummyUtilTestCaseModel.alias.admin_order_field,
                         "nullable")

        obj = DummyUtilTestCaseModel.objects.create(alias=DEFAULT)
        obj1 = DummyUtilTestCaseModel.objects.create()
        self.assertEqual(obj.alias, DEFAULT)
        self.assertEqual(obj.nullable, DEFAULT)

        obj.alias = VALUE
        self.assertEqual(obj.alias, VALUE)
        self.assertEqual(obj.nullable, VALUE)
        obj.save()
        obj = DummyUtilTestCaseModel.objects.get(pk=obj.pk)
        self.assertEqual(obj.alias, VALUE)
        self.assertEqual(obj.nullable, VALUE)

        obj.nullable = DEFAULT
        self.assertEqual(obj.alias, DEFAULT)
        self.assertEqual(obj.nullable, DEFAULT)

        del obj.alias
        self.assertIsNone(obj.alias)
        self.assertIsNone(obj.nullable)
        obj.save()
        obj = DummyUtilTestCaseModel.objects.get(pk=obj.pk)
        self.assertIsNone(obj.alias)
        self.assertIsNone(obj.nullable)

        obj.nullable = DEFAULT
        self.assertEqual(obj.alias, DEFAULT)
        self.assertEqual(obj.nullable, DEFAULT)
        obj.save()
        obj = DummyUtilTestCaseModel.objects.get(pk=obj.pk)
        self.assertEqual(obj.alias, DEFAULT)
        self.assertEqual(obj.nullable, DEFAULT)

        del obj.nullable
        self.assertIsNone(obj.alias)
        self.assertIsNone(obj.nullable)
        obj.save()
        obj = DummyUtilTestCaseModel.objects.get(pk=obj.pk)
        self.assertIsNone(obj.alias)
        self.assertIsNone(obj.nullable)

        # 未影响到其他model
        self.assertFalse(obj1.storage)
        self.assertFalse(obj1.c)
        obj1 = DummyUtilTestCaseModel.objects.get(pk=obj1.pk)
        self.assertFalse(obj1.storage)
        self.assertFalse(obj1.c)

        obj2 = DummyUtilTestCaseModel.objects.create()
        self.assertFalse(obj2.storage)
        self.assertFalse(obj2.c)
        obj1 = DummyUtilTestCaseModel.objects.get(pk=obj2.pk)
        self.assertFalse(obj2.storage)
        self.assertFalse(obj2.c)
