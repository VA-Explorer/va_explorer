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

@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """
    Return encoded URL parameters that are the same as the current
    request's parameters, only with the specified GET parameters added or changed.
    It also removes any empty parameters to keep things neat,
    so you can remove a parm by setting it to ``""``.
    For example, if you're on the page ``/things/?with_frosting=true&page=5``,
    then
    <a href="/things/?{% param_replace page=3 %}">Page 3</a>
    would expand to
    <a href="/things/?with_frosting=true&page=3">Page 3</a>
    Based on
    https://stackoverflow.com/questions/22734695/next-and-before-links-for-a-django-paginated-query/22735278#22735278
    """
    d = context['request'].GET.copy()
    for k, v in kwargs.items():
        d[k] = v
    for k in [k for k, v in d.items() if not v]:
        del d[k]
    return d.urlencode()