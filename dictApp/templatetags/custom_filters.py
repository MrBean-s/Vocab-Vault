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

@register.filter(name='times') 
def times(number):
    return range(number)

@register.filter
def divide(value, arg):
   try:
      return float(value) / float(arg)
   except (ValueError, ZeroDivisionError):
      return None

@register.filter
def modulo(value, arg):
   return int(value) % int(arg)