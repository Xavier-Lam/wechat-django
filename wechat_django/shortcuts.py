from functools import wraps

def wechat_required(app_name, scope, response):
    def decorator(func):
        @wraps
        def decorated_func(request, *args, **kwargs):
            return func(request, *args, **kwargs)
        return decorated_func
    return decorator