# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import threading
from uuid import uuid4

from ..utils.func import next_chunk, Static
from .base import WeChatTestCase


class UtilFunctoolTestCase(WeChatTestCase):
    def test_next_chunk(self):
        """测试next chunk"""
        data = list(next_chunk(range(50)))
        self.assertEqual(len(data), 1)
        self.assertEqual(set(range(50)), set(data[0]))

        data = list(next_chunk(range(100)))
        self.assertEqual(len(data), 1)
        self.assertEqual(set(range(100)), set(data[0]))

        data = list(next_chunk(range(101), 100))
        self.assertEqual(len(data), 2)
        self.assertEqual(set(range(100)), set(data[0]))
        self.assertEqual(set((100, )), set(data[1]))

    def test_static(self):
        """测试static"""
        total = 10
        strings = [str(uuid4()) for i in range(total)]
        another_strings = [s.encode().decode() for s in strings]

        for i in range(total):
            # 验证直接id不相等
            self.assertEqual(strings[i], another_strings[i])
            self.assertNotEqual(id(strings[i]), id(another_strings[i]))
            self.assertEqual(
                id(Static(strings[i])), id(Static(another_strings[i])))

        # 在另一个线程也正常
        def another_thread(strings):
            another_strings = [s.encode().decode() for s in strings]

            for i in range(total):
                # 验证直接id不相等
                self.assertEqual(strings[i], another_strings[i])
                self.assertNotEqual(id(strings[i]), id(another_strings[i]))
                self.assertEqual(
                    id(Static(strings[i])), id(Static(another_strings[i])))

        threading.Thread(target=another_thread, args=(strings,))
