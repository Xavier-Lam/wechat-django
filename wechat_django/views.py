from django.conf.urls import url
from django.http import response
import requests
from wechatpy.exceptions import WeChatClientException

from .handler import handler
from .models import WeChatApp

__all__ = ("material_proxy", "urls")

def material_proxy(request, appname, media_id):
    # TODO: cache
    app = WeChatApp.get_by_name(appname)
    if not app:
        return response.Http404()

    try:
        resp = app.client.material.get(media_id)
    except WeChatClientException as e:
        if e.errcode == 40007:
            return response.Http404()
        # TODO: 日志
        raise
    if not isinstance(resp, requests.Response):
        # 暂时只处理image和voice
        return response.Http404()
    
    rv = response.FileResponse(resp.content)
    for k, v in resp.headers.items():
        if k.lower().startswith("content-"):
            rv[k] = v
    return rv
    

url_patterns = (
    url(r"^(?P<appname>[-_a-zA-Z\d]+)/$", handler, name="handler"),
    url(
        r"^(?P<appname>[-_a-zA-Z\d]+)/materials/(?P<media_id>[_a-zA-Z\d]+)$", 
        material_proxy, 
        name="material_proxy"
    ),
)
urls = (url_patterns, "", "")