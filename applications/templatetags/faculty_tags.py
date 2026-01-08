from django import template
from applications.models import *

register = template.Library()

@register.filter
def count_level(items, level):
    if not items:
        return 0
    return sum(1 for i in items if getattr(i, "level", None) == level)


@register.simple_tag
def departments():
    return Department.objects.all()

@register.simple_tag
def designations():
    
    return Designation.objects.all()


@register.simple_tag
def degree():
    return Degree.objects.all()



@register.filter
def get_item(dictionary, key):
    if not dictionary:
        return None
    return dictionary.get(str(key))
