# -*- coding: utf-8 -*-
from __future__ import unicode_literals


def next_chunk(iterator, count=100):
    rv = []
    for item in iterator:
        rv.append(item)
        if len(rv) >= count:
            yield rv
            rv = []
    if rv:
        yield rv


class Static:
    __caches = dict()

    def __new__(cls, obj):
        if obj not in cls.__caches:
            cls.__caches[obj] = obj
        return cls.__caches[obj]

    def __init__(self, obj):
        pass
