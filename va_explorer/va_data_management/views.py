from django.shortcuts import render, redirect
from .models import VerbalAutopsy, CauseOfDeath, CauseCodingIssue, Location
from .forms import VerbalAutopsyForm
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import numpy as np


def index(request, page_size=15):
    absolute_page = int(request.GET.get('page', 1))

    relative_page = 1 if absolute_page == 1 else 2
    # only load current page, (if necessary) previous page, and (if necessary) next page of data
    start_id = (absolute_page - 1) * page_size + 1 
    stop_id = (absolute_page + relative_page) * page_size + 1
    va_ids = set(np.arange(start_id, stop_id)) 
    va_list = (VerbalAutopsy.objects
        .filter(pk__in=va_ids)
        .prefetch_related("location", "causes", "coding_issues")
        .order_by("id")
        )
    va_data = [{
        "id": va.id,
        "name": va.Id10007,
        "facility": va.location.name,
        "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
        "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
        "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
    } for va in va_list]
    paginator = Paginator(va_data, page_size)  # 30 posts in each page
    #try:
    va_page_data = paginator.page(relative_page)
    # except PageNotAnInteger:
    #     # If page is not an integer deliver the first page
    #     va_page_data = paginator.page(1)
    # except EmptyPage:
    #     # If page is out of range deliver last page of results
    #     va_page_data = paginator.page(paginator.num_pages)

    context = {"va_data": va_page_data, "page": relative_page}
    # return render(request,
    #               "va_data_management/index.html",
    #               {'page': page,
    #                'post_list': post_list})
    return render(request, "va_data_management/index.html", context)

# TODO: Use standard django CRUD conventions; e.g. see https://stackoverflow.com/questions/4673985/how-to-update-an-object-from-edit-form-in-django

# TODO: Is the convention to use pk instead of id in django?
def show(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(None, instance=va)
    coding_issues = va.coding_issues.all()
    warnings = [issue for issue in coding_issues if issue.severity == 'warning']
    errors = [issue for issue in coding_issues if issue.severity == 'error']
    history = va.history.all().reverse()
    history_pairs = zip(history, history[1:])
    diffs = [new.diff_against(old) for (old, new) in history_pairs]
    # TODO: date in diff info should be formatted in local time
    # TODO: history should eventually show user who made the change
    context = { "id": id, "form": form, "warnings": warnings, "errors": errors, "diffs": diffs }
    return render(request, "va_data_management/show.html", context)

def edit(request, id):
    # TODO: We only want to allow editing of some fields
    # TODO: We want to provide context for all the fields
    # TODO: We probably want to use a django Form here or crispy forms
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(None, instance=va)
    context = { "id": id, "form": form }
    return render(request, "va_data_management/edit.html", context)

def save(request, id):
    # TODO: There are probably more appropriate ways to handle form editing in django
    # TODO: When a record is changed, should it automatically be recoded if it was already coded?
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(request.POST, instance=va)
    if form.is_valid():
        form.save()
    return redirect("va_data_management:show", id=id)

# Reset to the first historical record
# TODO: If a record is reset, should it automatically be recoded?
def reset(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    earliest = va.history.earliest()
    latest = va.history.latest()
    if earliest and len(latest.diff_against(earliest).changes) > 0:
        earliest.instance.save()
    return redirect("va_data_management:show", id=id)

# Revert the most recent change
# TODO: Should record automatically be recoded?
def revert_latest(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    if va.history.count() > 1:
        previous = va.history.all()[1]
        latest = va.history.latest()
        if len(latest.diff_against(previous).changes) > 0:
            previous.instance.save()
        return redirect("va_data_management:show", id=id)
