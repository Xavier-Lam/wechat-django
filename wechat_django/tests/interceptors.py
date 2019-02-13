import json
from httmock import all_requests, HTTMock, response, urlmatch

TESTFORBIDDEN = -99999


def common_interceptor(callback, **kwargs):
    decorator = urlmatch(**kwargs) if kwargs else all_requests
    mock = decorator(callback)
    return HTTMock(mock)


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
            callback(url, request, response)
        return resp

    return HTTMock(wechatapi_mock)


def wechatapi_accesstoken(callback=None):
    return wechatapi("/cgi-bin/token", {
        "access_token": "ACCESS_TOKEN",
        "expires_in": 7200
    }, callback)


def wechatapi_error(api):
    return wechatapi(api, {
        "errcode": TESTFORBIDDEN,
        "errmsg": "",
    })
