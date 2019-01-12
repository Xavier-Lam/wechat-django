from django.conf.urls import url

from .handler import handler

urls = (
    url(r"^(?P<appname>[-_a-zA-Z]+)$", handler, name="handler"),
)