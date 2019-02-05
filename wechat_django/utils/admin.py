from django.urls import reverse

def linkify(field_name):
    """
    Converts a foreign key value into clickable links.

    If field_name is 'parent', link text will be str(obj.parent)
    Link will be admin url for the admin url for obj.parent.id:change
    """
    def _linkify(obj):
        app_label = obj._meta.app_label
        linked_obj = getattr(obj, field_name)
        model_name = linked_obj._meta.model_name
        view_name = "admin:{app_label}_{model_name}_change".format(
            app_label=app_label,
            model_name=model_name
        )
        link_url = reverse(view_name, args=[linked_obj.id])
        link_url += "?app_id={0}".format(obj.app.id)
        return '<a href="{0}">{1}</a>'.format(link_url, linked_obj)

    _linkify.short_description = field_name # TODO: 改为_
    _linkify.allow_tags = True
    _linkify.admin_order_field = field_name
    return _linkify