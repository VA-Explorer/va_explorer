from django.shortcuts import render
from .models import VerbalAutopsy, CauseOfDeath, CauseCodingIssue

def index(request):
    va_list = VerbalAutopsy.objects.prefetch_related("causes", "coding_issues")
    context = { "va_list": va_list }
    return render(request, "va_data_management/index.html", context)
