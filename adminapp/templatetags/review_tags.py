from django import template
import math

register = template.Library()

@register.filter
def full_stars(value):
    if not value:
        return range(0)
    return range(int(math.floor(value)))

@register.filter
def empty_stars(value):
    if not value:
        return range(5)
    return range(5 - int(math.floor(value)))
