from functools import wraps

from django.http import response as django_response
from django.urls.base import reverse
from django.views.decorators.csrf import csrf_exempt

from wechat_django.rest_framework.views import APIView


class WeChatViewMixin:
    """微信相关业务的View"""

    include_application_classes = None
    exclude_application_classes = None

    url_pattern = None
    """注册的url pattern"""

    url_name = None
    """注册的url名"""

    def initialize_request(self, request, *args, **kwargs):
        request = super().initialize_request(request, *args, **kwargs)
        self.get_app(request, *args, **kwargs)
        return request

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.exclude_application_classes:
            if isinstance(request.wechat_app,
                          self.exclude_application_classes):
                raise django_response.Http404
        if self.include_application_classes:
            if not isinstance(request.wechat_app,
                              self.include_application_classes):
                raise django_response.Http404

    def finalize_response(self, request, response, *args, **kwargs):
        if isinstance(response, str):
            response = django_response.HttpResponse(response)
        elif isinstance(response, dict):
            response = django_response.JsonResponse(response)
        return super().finalize_response(request, response, *args, **kwargs)

    @classmethod
    def as_view(cls, **kwargs):
        view = super().as_view(**kwargs)
        return csrf_exempt(view)

    def get_app(self, request, *args, **kwargs):
        if not hasattr(request, "wechat_app"):
            from wechat_django.models import Application

            app_name = self.get_app_name(request, *args, **kwargs)
            request.wechat_app = Application.objects.get(name=app_name)
        return request.wechat_app

    def get_app_name(self, request, *args, **kwargs):
        return kwargs["app_name"].replace("/", ".")

    @classmethod
    def get_url(cls, wechat_app, *args, **kwargs):
        kwargs.update({"app_name": wechat_app.name})
        url_name = "{0}:{1}".format("wechat_django", cls.url_name)
        return reverse(url_name, args=args, kwargs=kwargs)


class WeChatView(WeChatViewMixin, APIView):
    pass


def wechat_view(regex, name=None, methods=None, bind=False):
    """函数view装饰器,方便生成非class-based View"""

    methods = methods or ("GET",)

    def decorator(func):
        @wraps(func)
        def view(self, request, *args, **kwargs):
            return func(request, *args, **kwargs)

        attrs = {method.lower(): func if bind else view for method in methods}
        attrs["url_pattern"] = regex
        attrs["url_name"] = name
        return type("WeChatView", (WeChatView,), attrs)

    return decorator
