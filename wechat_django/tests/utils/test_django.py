from django.test import TestCase
from django_fake_model import models as f

from wechat_django.utils.django import decriptor2contributor


class DummyDescriptor:
    value = None

    def __init__(self, arg):
        self.arg = arg

    def __get__(self, obj, objtype):
        return self.owner, self.name, self.arg, obj, self.value

    def __set__(self, obj, value):
        self.value = value

    def __delete__(self, obj):
        self.value = ""

    def __set_name__(self, owner, name):
        self.owner = owner
        self.name = name

    def formfield(self):
        return self.name

    def hidden_method(self):
        pass


ARG = "arg"
VALUE = "value"

contributor = decriptor2contributor(DummyDescriptor)


class DummyDjangoTestCaseModel(f.FakeModel):
    attr = contributor(ARG)


class DjangoTestCase(TestCase):
    @DummyDjangoTestCaseModel.fake_me
    def test_decriptor2contributor(self):
        """测试Descriptor转Contributor"""
        model = DummyDjangoTestCaseModel()
        model.attr = VALUE
        owner, name, arg, obj, value = model.attr
        self.assertIs(owner, DummyDjangoTestCaseModel)
        self.assertEqual(name, "attr")
        self.assertEqual(arg, ARG)
        self.assertIs(obj, model)
        self.assertEqual(value, VALUE)

        del model.attr
        owner, name, arg, obj, value = model.attr
        self.assertEqual(value, "")

        self.assertEqual(DummyDjangoTestCaseModel.attr.formfield(), "attr")
        self.assertRaises(AttributeError,
                          lambda: DummyDjangoTestCaseModel.attr.hidden_method)
