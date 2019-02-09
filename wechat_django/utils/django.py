import re

from django.utils.translation import ugettext as _

def enum2choices(enum):
    pattern = re.compile("^[A-Z][A-Z_\d]+$")
    return tuple(
        (getattr(enum, key), _(key))
        for key in dir(enum)
        if re.match(pattern, key)
    )

def get_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip