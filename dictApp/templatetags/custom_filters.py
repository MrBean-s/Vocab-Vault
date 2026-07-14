from django import template
register = template.Library()

@register.filter
def get_at(list_obj, index):
    try:
        return list_obj[index]
    except IndexError:
        return None

@register.filter
def split(value, sep=None):
    if sep:
        return value.split(sep)
    return value.split()