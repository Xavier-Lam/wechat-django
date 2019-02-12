from .bases import WeChatTestCase

class OAuthTestCase(WeChatTestCase):
    def test_oauth(self):
        """测试oauth接口请求"""
        pass

    def test_unauthorization_response(self):
        """测试未授权响应"""
        # 不要求授权
        pass
        # 默认响应
        pass
        # 有redirect_uri的响应
        pass
        # 传入Response对象的响应
        pass
        # 传入Response处理函数的响应
        pass
    
    def test_session(self):
        """测试授权后session状态保持"""
        pass