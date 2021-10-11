from django.conf import settings
from django.core.management.utils import get_random_secret_key
from django.test import TestCase
from django.utils.functional import empty

from wechat_django.utils.crypto import crypto, Crypto


class UtilCryptoTestCase(TestCase):
    def test_crypto(self):
        """测试加解密"""
        # 测试3种不同密钥长度
        for i in range(3):
            for _ in range(5):
                key = get_random_secret_key()[: i + 31]
                crypto = Crypto(key)
                # 测试不同的加密长度
                for i in range(33):
                    for _ in range(5):
                        value = get_random_secret_key()[: i + 1]
                        encrypted = crypto.encrypt(value)
                        self.assertEqual(crypto.decrypt(encrypted), value)

        # 测试
        encrypted = crypto.encrypt("")
        self.assertEqual(encrypted, "")
        self.assertEqual(crypto.decrypt(encrypted), "")

        # 测试raw输出
        s = get_random_secret_key()[:32]
        encrypted = crypto.encrypt(s.encode(), raw=True)
        self.assertEqual(crypto.decrypt(encrypted), s)

    def test_default_crypto(self):
        """测试默认crypto"""
        data = get_random_secret_key()[:32]
        c = Crypto(settings.SECRET_KEY)
        encrypted = crypto.encrypt(data)
        self.assertEqual(c.encrypt(data), encrypted)
        self.assertEqual(crypto.decrypt(encrypted), data)

    def test_empty_key(self):
        """测试不加密状况"""
        with self.settings(WECHAT_DJANGO_SECRET_KEY=None):
            crypto._wrapped = empty

            data = get_random_secret_key()[:5]
            self.assertEqual(crypto.encrypt(data), data)
            self.assertEqual(crypto.encrypt(data, raw=True), data.encode())
            self.assertEqual(crypto.encrypt(data.encode(), raw=True),
                             data.encode())
            self.assertEqual(crypto.decrypt(data), data)
            self.assertEqual(crypto.decrypt(data.encode()), data)

            crypto._wrapped = empty
