import re

from django import template
from django.urls import NoReverseMatch, reverse

from va_explorer.va_data_management.models import PII_FIELDS
from va_explorer.va_data_management.models import REDACTED_STRING

register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, pattern_or_url):
    try:
        pattern = reverse(pattern_or_url)
    except NoReverseMatch:
        pattern = pattern_or_url

    path = context["request"].path

    if re.search(pattern, path):
        return "active"
    return ""


@register.simple_tag(takes_context=True)
def pii_filter(context, field, value):
    if field in PII_FIELDS and not context['user'].can_view_pii:
        return REDACTED_STRING
    return value
