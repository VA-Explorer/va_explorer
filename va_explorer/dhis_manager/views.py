from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from va_explorer.va_data_management.management.commands.run_dhis import Command
from va_explorer.va_data_management.models import dhisStatus,VerbalAutopsy
# Create your views here.

@login_required
def index(request):
    # to subset few rows,add at the end [:10] for 10 rows etc..
    # exclude vas that have no dhis2 status; not pushed
    push = "notyet"
    vadata = VerbalAutopsy.objects.filter(causes__isnull=False,dhisva__isnull=True).count()
    valist = VerbalAutopsy.objects.filter(causes__isnull=False, dhisva__isnull=True)
    list1 = list()
    for va in valist:
        list1.append(va.id)

    context = {
        "vanum":str(vadata),
        "valist":list1,
        "push":push
    }
    return render(request,"pages/dhis.html",context)


@login_required
def pushDHIS(request):
    cl = Command()
    numPushed,numTotal,status = cl.handle()
    btnpush = 'OK'
    if status=='SUCCESS':
        txt = "successfully posted "+str(numPushed)+" out of "+str(numTotal)+" records"
    else:
        txt = "push failed"

    context = {
        "txt":txt,
        "btnpush":btnpush
    }
    return render(request,"pages/dhis.html",context)
