from functools import wraps

from django.utils.decorators import available_attrs

def message_handler(view_func):
    """
    Marks a view function as being exempt from the CSRF view protection.
    """
    # 防止副作用
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)
    wrapped_view.message_handler = True
    return wraps(view_func, assigned=available_attrs(view_func))(wrapped_view)