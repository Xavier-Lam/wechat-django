class AbilityError(NotImplementedError):
    """应用能力缺失"""


class BadMessageRequest(ValueError):
    """推送消息请求异常"""


class JSAPIError(ValueError):
    """JSAPI请求错误"""
