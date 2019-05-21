# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.dispatch import Signal


order_updated = Signal(["result", "order", "state", "attach"])
