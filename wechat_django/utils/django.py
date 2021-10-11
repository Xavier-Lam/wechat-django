from functools import partial


ALLOWED_ATTRS = [
    "admin_order_field",
    "choices",
    "default",
    "formfield",
    "help_text",
    "name",
    "null",
    "verbose_name"
]


def decriptor2contributor(Descriptor, allowed_attrs=ALLOWED_ATTRS):
    """Transform a python descriptor into a django contributor"""

    def __new__(cls, *args, **kwargs):
        self = object.__new__(cls)
        self._descriptor = Descriptor(*args, **kwargs)
        return self

    def contribute_to_class(self, cls, name):
        descriptor = self._descriptor

        if hasattr(descriptor, "__set_name__"):
            descriptor.__set_name__(cls, name)

        kwargs = {}
        if hasattr(descriptor, "__get__"):
            kwargs["fget"] = partial(descriptor.__get__, objtype=None)
        if hasattr(descriptor, "__set__"):
            kwargs["fset"] = descriptor.__set__
        if hasattr(descriptor, "__delete__"):
            kwargs["fdel"] = descriptor.__delete__

        # 迁移属性
        prop = type(Descriptor.__name__, (property,), {})(**kwargs)
        for attr_name in allowed_attrs:
            if hasattr(descriptor, attr_name):
                attr = getattr(descriptor, attr_name)
                if callable(attr):
                    attr = attr.__get__(descriptor, Descriptor)
                else:
                    attr = getattr(descriptor, attr_name)
                setattr(prop, attr_name, attr)
        setattr(cls, name, prop)

        if hasattr(descriptor, "contribute_to_class"):
            descriptor.contribute_to_class(cls, name)

    return type(
        Descriptor.__name__,
        (object,),
        dict(
            __new__=__new__,
            contribute_to_class=contribute_to_class
        )
    )
