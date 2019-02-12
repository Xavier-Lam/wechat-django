import json
from httmock import HTTMock, response, urlmatch

from ..exceptions import WeChatApiError

def wechatapi(api, data="", callback=None):
    @urlmatch(netloc=r"(.*\.)?api\.weixin\.qq\.com$", path=api)
    def wechatapi_mock(url, request):
        if url.path != api:
            return response(404)
        headers = {
            "Content-Type": "application/json"
        }
        resp = response(200, data, headers)
        if callback:
            callback(request, response)
        return resp

    return HTTMock(wechatapi_mock)

def wechat_api_accesstoken():
    return wechatapi("/cgi-bin/token", {
        "access_token": "ACCESS_TOKEN",
        "expires_in": 7200
    })

def wechatapi_error(api):
    return wechatapi(api, {
        "errcode": WeChatApiError.TESTFORBIDDEN,
        "errmsg": "",
    })