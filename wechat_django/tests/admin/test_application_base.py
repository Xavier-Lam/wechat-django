from django import forms

from wechat_django.admin.app.base import EncryptedField
from wechat_django.utils.crypto import crypto
from ..base import WeChatDjangoTestCase


class ApplicationBaseTestCase(WeChatDjangoTestCase):
    def test_encrypt_field(self):
        """测试EncryptField"""
        class DummyForm(forms.Form):
            plain = EncryptedField(required=False)
            raw = EncryptedField(raw=True, required=False)

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                for name, field in self.fields.items():
                    if name in self.initial:
                        field.initial = self.initial[name]

        data = {
            "plain": "plain",
            "raw": "raw"
        }

        # TODO: 渲染空白表单
        pass

        # 填充空值
        form = DummyForm({})
        self.assertTrue(form.is_valid())
        self.assertNotIn("plain", form.changed_data)
        self.assertNotIn("raw", form.changed_data)
        cleaned_data = form.cleaned_data
        self.assertEqual(form.cleaned_data["plain"], "")
        self.assertEqual(form.cleaned_data["raw"], b"")

        # 首次填充
        form = DummyForm(data)
        self.assertTrue(form.is_valid())
        self.assertIn("plain", form.changed_data)
        self.assertIn("raw", form.changed_data)
        self.assertEqual(crypto.decrypt(form.cleaned_data["plain"]),
                         data["plain"])
        self.assertEqual(crypto.decrypt(form.cleaned_data["raw"]),
                         data["raw"])
        cleaned_data = form.cleaned_data

        # 重新填充相同值
        form = DummyForm(data, initial=cleaned_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.changed_data)
        self.assertEqual(crypto.decrypt(form.cleaned_data["plain"]),
                         data["plain"])
        self.assertEqual(crypto.decrypt(form.cleaned_data["raw"]),
                         data["raw"])

        # 未进行修改
        formdata = {
            "plain": DummyForm.base_fields["plain"].prepare_value(
                cleaned_data["plain"]),
            "raw": DummyForm.base_fields["raw"].prepare_value(
                cleaned_data["raw"])
        }
        form = DummyForm(formdata, initial=cleaned_data)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.changed_data)
        self.assertEqual(crypto.decrypt(form.cleaned_data["plain"]),
                         data["plain"])
        self.assertEqual(crypto.decrypt(form.cleaned_data["raw"]),
                         data["raw"])

        # 修改为空值
        formdata = {
            "plain": "",
            "raw": ""
        }
        form = DummyForm(formdata, initial=cleaned_data)
        self.assertTrue(form.is_valid())
        self.assertIn("plain", form.changed_data)
        self.assertIn("raw", form.changed_data)
        self.assertEqual(form.cleaned_data["plain"], "")
        self.assertEqual(form.cleaned_data["raw"], b"")

        # TODO: 渲染提交错误的表单
        pass

        # 一般修改
        data = {
            "plain": "plain2",
            "raw": "raw2"
        }
        form = DummyForm(data, initial=cleaned_data)
        self.assertTrue(form.is_valid())
        self.assertIn("plain", form.changed_data)
        self.assertIn("raw", form.changed_data)
        self.assertEqual(crypto.decrypt(form.cleaned_data["plain"]),
                         data["plain"])
        self.assertEqual(crypto.decrypt(form.cleaned_data["raw"]),
                         data["raw"])
