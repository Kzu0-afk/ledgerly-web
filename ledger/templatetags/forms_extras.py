from django import template

register = template.Library()


@register.filter(name="add_class")
def add_class(field, css_class: str):
    """Append CSS classes to a form field widget safely."""
    existing = field.field.widget.attrs.get("class", "").strip()
    combined = (existing + " " + (css_class or "")).strip()
    return field.as_widget(attrs={**field.field.widget.attrs, "class": combined})


@register.filter(name="add_attrs")
def add_attrs(field, arg: str):
    """Add arbitrary attributes via 'key1:value1,key2:value2'."""
    attrs = {}
    if arg:
        for pair in arg.split(","):
            if ":" in pair:
                key, value = pair.split(":", 1)
                attrs[key.strip()] = value.strip()
    return field.as_widget(attrs={**field.field.widget.attrs, **attrs})


