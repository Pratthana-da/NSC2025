# classroom/templatetags/custom_filters.py
from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    if isinstance(field, BoundField):
        return field.as_widget(attrs={"class": css})
    return field  # ป้องกัน error ถ้าไม่ใช่ BoundField

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)