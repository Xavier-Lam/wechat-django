import json
import os

from httmock import HTTMock, response, urlmatch

from django.test import TestCase

from wechat_django.models import WeChatApp

_TESTS_PATH = os.path.abspath(os.path.dirname(__file__))
_FIXTURE_PATH = os.path.join(_TESTS_PATH, 'fixtures')

@urlmatch(netloc=r'(.*\.)?api\.weixin\.qq\.com$')
def wechat_api_mock(url, request):
    path = url.path.replace('/cgi-bin/', '').replace('/', '_')
    if path.startswith('_'):
        path = path[1:]
    res_file = os.path.join(_FIXTURE_PATH, '%s.json' % path)
    content = {
        'errcode': 99999,
        'errmsg': 'can not find fixture %s' % res_file,
    }
    headers = {
        'Content-Type': 'application/json'
    }
    try:
        with open(res_file, 'rb') as f:
            content = json.loads(f.read().decode('utf-8'))
    except (IOError, ValueError) as e:
        content['errmsg'] = 'Loads fixture {0} failed, error: {1}'.format(
            res_file,
            e
        )
    return response(200, content, headers, request=request)

class WeChatTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        WeChatApp(title="test", name="test", 
            appid="appid", appsecret="secret").save()
        WeChatApp(title="test1", name="test1", 
            appid="appid1", appsecret="secret").save()