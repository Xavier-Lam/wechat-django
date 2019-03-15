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
