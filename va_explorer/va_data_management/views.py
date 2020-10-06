from django.shortcuts import render, redirect
from .models import VerbalAutopsy, CauseOfDeath, CauseCodingIssue, Location
from .forms import VerbalAutopsyForm

def index(request):
    va_list = VerbalAutopsy.objects.prefetch_related("causes", "coding_issues").order_by("id")
    va_data = [{
        "id": va.id,
        "name": va.Id10007,
        "facility": va.location.name,
        "cause": va.causes.first().cause if va.causes.first() else "",
        "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
        "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
    } for va in va_list]
    context = { "va_data": va_data }
    return render(request, "va_data_management/index.html", context)

# TODO: Use standard django CRUD conventions; e.g. see https://stackoverflow.com/questions/4673985/how-to-update-an-object-from-edit-form-in-django

# TODO: Is the convention to use pk instead of id in django?
def show(request, id):
    # TODO: The use of values() to get a dictionary is probably not ideal
    # and is perhaps more fragile than va = VerbalAutopsy.objects.get(id=id)
    va = VerbalAutopsy.objects.filter(id=id).values()[0]
    del va["id"]
    del va["location_id"]
    coding_issues = CauseCodingIssue.objects.filter(verbalautopsy_id=id)
    warnings = [issue for issue in coding_issues if issue.severity == 'warning']
    errors = [issue for issue in coding_issues if issue.severity == 'error']
    context = { "id": id, "va": va, "warnings": warnings, "errors": errors }
    return render(request, "va_data_management/show.html", context)

def edit(request, id):
    # TODO: The use of values() to get a dictionary is probably not ideal
    # and is perhaps more fragile than va = VerbalAutopsy.objects.get(id=id)
    # TODO: We only want to allow editing of some fields
    # TODO: We want to provide context for all the fields
    # TODO: We probably want to use a django Form here or crispy forms
    va = VerbalAutopsy.objects.filter(id=id).values()[0]
    del va["id"]
    del va["location_id"]
    context = { "id": id, "va": va }
    return render(request, "va_data_management/edit.html", context)

def save(request, id):
    # TODO: There are probably more appropriate ways to handle form editing in django
    va = VerbalAutopsy.objects.get(id=id)
    form = VerbalAutopsyForm(request.POST, instance=va)
    if form.is_valid():
        form.save()
    return redirect('va_data_management:show', id=id)
