from django import template
 
register = template.Library()
 
@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr, 0) or 0
 
@register.filter
def get_dict(d, key):
    return d.get(key, 0) or 0
 