# -*- coding: utf-8 -*-
from __future__ import unicode_literals


class DelayPropertyDescriptor(object):
    def __init__(self, delayed):
        self.delayed = delayed

    def __get__(self, instance, instance_type=None):
        if not hasattr(self, "_value"):
            self._value = self.delayed.func(instance)
        return self._value


class DelayProperty(object):
    def __init__(self, func):
        self.func = func

    def add2cls(self, cls, name):
        setattr(cls, name, DelayPropertyDescriptor(self))


def DelayProperty(self, func):
    def getter(self):
        pass

    return property(getter)
