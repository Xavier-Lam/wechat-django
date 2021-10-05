import base64
from django.utils.functional import SimpleLazyObject

from wechatpy.crypto.base import WeChatCipher

from .django import get_setting


class Crypto:
    def __init__(self, key):
        key = self._fix_key(key)
        self.cipher = WeChatCipher(key)

    def encrypt(self, value, raw=False):
        value = value or ""
        if not value:
            return value.encode() if raw else value
        value = self._fix_value(value)
        encypted_value = self.cipher.encrypt(value)
        if raw:
            return encypted_value
        return base64.b64encode(encypted_value).decode()

    def decrypt(self, data):
        if not data:
            return data
        if isinstance(data, str):
            data = base64.b64decode(data.encode())
        decypted_value = self.cipher.decrypt(data)
        return self._fix_decrypted_value(decypted_value)

    def _fix_key(self, key):
        if isinstance(key, str):
            key = key.encode()
        a, b = divmod(32, len(key))
        if a:
            return key*a + key[:b]
        else:
            return key[:32]

    def _fix_value(self, value):
        if isinstance(value, str):
            value = value.strip().encode()
        if len(value) % 32:
            pad = 32 - len(value) % 32
            value = value + b"\0"*pad
        return value

    def _fix_decrypted_value(self, value):
        return value.decode().strip("\0")


class DefaultCrypto(Crypto):
    def __init__(self):
        key = get_setting("SECRET_KEY")
        key and super().__init__(key)

    def encrypt(self, value, raw=False):
        if hasattr(self, "cipher"):
            return super().encrypt(value, raw=raw)
        else:
            if raw and isinstance(value, str):
                value = value.encode()
            elif not raw and not isinstance(value, str):
                value = value.decode()
            return value

    def decrypt(self, data):
        if hasattr(self, "cipher"):
            return super().decrypt(data)
        else:
            if not isinstance(data, str):
                data = data.decode()
            return data


crypto = SimpleLazyObject(DefaultCrypto)
