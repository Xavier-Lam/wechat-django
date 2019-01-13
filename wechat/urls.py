from django.conf.urls import url

from .handler import handler

url_patterns = (
    url(r"^(?P<appname>[-_a-zA-Z]+)/$", handler, name="handler"),
)
urls = (url_patterns, "", "")