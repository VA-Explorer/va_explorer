from django.shortcuts import render, redirect
from django.forms.models import model_to_dict
from .models import VerbalAutopsy, CauseOfDeath, CauseCodingIssue, Location
from .forms import VerbalAutopsyForm

def index(request):
    va_list = VerbalAutopsy.objects.prefetch_related("location", "causes", "coding_issues").order_by("id")
    va_data = [{
        "id": va.id,
        "name": va.Id10007,
        "facility": va.location.name,
        "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
        "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
        "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
    } for va in va_list]
    context = { "va_data": va_data }
    return render(request, "va_data_management/index.html", context)

# TODO: Use standard django CRUD conventions; e.g. see https://stackoverflow.com/questions/4673985/how-to-update-an-object-from-edit-form-in-django

# TODO: Is the convention to use pk instead of id in django?
def show(request, id):
    va = VerbalAutopsy.objects.get(id=id)
    coding_issues = va.coding_issues.all()
    warnings = [issue for issue in coding_issues if issue.severity == 'warning']
    errors = [issue for issue in coding_issues if issue.severity == 'error']
    history = va.history.all().reverse()
    history_pairs = zip(history, history[1:])
    diffs = [new.diff_against(old) for (old, new) in history_pairs]
    # TODO: date in diff info should be formatted in local time
    # TODO: history should eventually show user who made the change
    context = { "id": id, "va": model_to_dict(va, exclude=("id", "location")), "warnings": warnings, "errors": errors, "diffs": diffs }
    return render(request, "va_data_management/show.html", context)

def edit(request, id):
    # TODO: We only want to allow editing of some fields
    # TODO: We want to provide context for all the fields
    # TODO: We probably want to use a django Form here or crispy forms
    va = VerbalAutopsy.objects.get(id=id)
    context = { "id": id, "va": model_to_dict(va, exclude=("id", "location")) }
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
