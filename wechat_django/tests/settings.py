# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
from django.conf.urls import url
import wechat_django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_HOSTS = ["example.com"]

SECRET_KEY = "fake-key"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "wechat_django",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

urlpatterns = [
    url(r'^wechat/', wechat_django.urls)
]

ROOT_URLCONF = "wechat_django.tests.settings"
