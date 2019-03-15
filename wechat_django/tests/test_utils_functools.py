# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ..utils.func import next_chunk
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
