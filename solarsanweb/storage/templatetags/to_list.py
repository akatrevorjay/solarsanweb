from django import template
register = template.Library()


@register.filter
def to_list(value):
    """Creates a list from an iterable"""
    return list(value)
