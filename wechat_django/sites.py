from django.conf.urls import include, url
from django.utils.functional import cached_property, SimpleLazyObject


class WeChatSite:
    name = "wechat_django"

    base_url = r"^(?P<app_name>[-a-zA-Z0-9_\.]+)/"

    def __init__(self):
        self._registered_views = []

    def register(self, cls):
        self._registered_views.append(cls)
        return cls

    def unregister(self, cls):
        self._registered_views.remove(cls)

    def get_urls(self):
        return [
            url(self.base_url, include([
                url(
                    cls.url_pattern,
                    self._create_view(cls),
                    name=cls.url_name
                )
            ]))
            for cls in self._registered_views
        ]

    @cached_property
    def urls(self):
        return self.get_urls(), "wechat_django", self.name

    def _create_view(self, cls):
        return cls.as_view()


default_site = SimpleLazyObject(WeChatSite)
"""默认微信站点,适用于一般状况"""
