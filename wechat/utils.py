import re

def enum2choices(enum):
    pattern = re.compile("^[A-Z][A-Z_]+$")
    return tuple(
        (key, getattr(enum, key))
        for key in dir(enum)
        if re.match(pattern, key)
    )