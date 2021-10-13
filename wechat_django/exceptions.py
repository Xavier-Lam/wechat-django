class AbilityError(NotImplementedError):
    """This application do not have ability to do something"""


class BadMessageRequest(ValueError):
    """Received an abnormal message in message handler"""


class JSAPIError(ValueError):
    """An error occurred when using WeChat's JSAPI"""
