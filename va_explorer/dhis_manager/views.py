from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from va_explorer.va_data_management.management.commands.run_dhis import Command
from va_explorer.va_data_management.models import dhisStatus,VerbalAutopsy
import environ
# Create your views here.

@login_required
def index(request):
    # to subset few rows,add at the end [:10] for 10 rows etc..
    # exclude vas that have no dhis2 status; not pushed
    push = "notyet"
    env = environ.Env()

    # DHIS2 VARIABLES
    DHIS2_USER = env("DHIS2_USER")
    DHIS2_PASS = env("DHIS2_PASS")

    cmd = Command()
    auth = (DHIS2_USER,DHIS2_PASS)
    eventsnum = cmd.getEventsValues('sv91bCroFFx', auth)
    cmd.syncDHISStatus()
    events = cmd.getPushedVA('sv91bCroFFx', auth)

    valist = VerbalAutopsy.objects.filter(causes__isnull=False, dhisva__isnull=True).values_list('id',flat=True)
    list1 = list(valist)
    list1 = [str(i) for i in list1]

    list3 = list()
    for x in list1:
        if x not in events:
            list3.append(x)

    #vadata = VerbalAutopsy.objects.filter(causes__isnull=False, dhisva__isnull=True).count()

    context = {
        "vanum":str(len(list3)),
        "total":str(eventsnum),
        "push":push
    }
    return render(request,"pages/dhis.html",context)


@login_required
def pushDHIS(request):

    env = environ.Env()
    # DHIS2 VARIABLES
    DHIS2_USER = env("DHIS2_USER")
    DHIS2_PASS = env("DHIS2_PASS")

    cmd = Command()
    auth = (DHIS2_USER, DHIS2_PASS)
    #eventsnum = cmd.getEventsValues('sv91bCroFFx', auth)
    va_in_dhis2 = cmd.getPushedVA('sv91bCroFFx', auth)
    eventsnum = len(va_in_dhis2)
    dhisdata = [int(i) for i in va_in_dhis2]

    #cmd.syncDHISStatus()
    vadata = VerbalAutopsy.objects.filter(causes__isnull=False, dhisva__isnull=True).exclude(id__in=dhisdata).count()
    if vadata>0:
        numPushed,numTotal,status = cmd.handle()
    else:
        cmd.syncDHISStatus()
        status = 'Nothing to push'
    btnpush = 'OK'

    if status=='SUCCESS':
        txt = "successfully posted "+str(numPushed)+" out of "+str(numTotal)+" records"
    else:
        txt = "Nothing to Post!"

    context = {
        "txt":txt,
        "vanum": str(vadata),
        "btnpush":btnpush,
        'total':eventsnum
    }
    return render(request,"pages/dhis.html",context)
