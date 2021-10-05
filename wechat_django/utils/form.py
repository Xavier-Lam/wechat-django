from django import forms
from django.db.models.fields import Field


class ModelFormMetaclass(forms.models.ModelFormMetaclass):
    def __new__(mcs, name, bases, attrs):
        # 增加formfield
        if "Meta" in attrs and hasattr(attrs["Meta"], "fields"):
            attrs["auto_declared_fields"] = []
            exclude = getattr(attrs["Meta"], "exclude", tuple())
            formfield_callback = getattr(attrs["Meta"], "formfield_callback",
                                         None)
            for field in attrs["Meta"].fields:
                attr = getattr(attrs["Meta"].model, field, None)
                if not isinstance(attr, Field)\
                   and isinstance(attr, property)\
                   and hasattr(attr, "formfield")\
                   and field not in exclude:
                    kwargs = {}
                    widgets = getattr(attrs["Meta"], "widgets", {})
                    if field in widgets:
                        kwargs["widget"] = widgets[field]
                    if formfield_callback:
                        formfield = formfield_callback(attr, **kwargs)
                    else:
                        formfield = attr.formfield(**kwargs)
                    attrs[field] = formfield
                    attrs["auto_declared_fields"].append(field)
        return super().__new__(mcs, name, bases, attrs)


class ModelForm(forms.BaseModelForm, metaclass=ModelFormMetaclass):
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        if instance:
            initial = kwargs.pop("initial", {})
            for field in self.auto_declared_fields:
                initial[field] = getattr(instance, field)
            kwargs["initial"] = initial
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        for field in self.auto_declared_fields:
            if field in self.changed_data:
                setattr(self.instance, field, self.cleaned_data[field])
        return super().save(commit=commit)
