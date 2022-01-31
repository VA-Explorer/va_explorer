import environ
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView

from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.management.commands.run_dhis import Command
from va_explorer.va_data_management.models import VerbalAutopsy


class IndexView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "pages/dhis.html"
    permission_required = "dhis_manager.change_dhisstatus"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        push = "notyet"
        env = environ.Env()

        # DHIS2 VARIABLES
        DHIS2_USER = env("DHIS2_USER")
        DHIS2_PASS = env("DHIS2_PASS")

        cmd = Command()
        auth = (DHIS2_USER, DHIS2_PASS)
        eventsnum = cmd.getEventsValues("sv91bCroFFx", auth)
        cmd.syncDHISStatus()
        events = cmd.getPushedVA("sv91bCroFFx", auth)

        valist = VerbalAutopsy.objects.filter(
            causes__isnull=False, dhisva__isnull=True
        ).values_list("id", flat=True)
        list1 = list(valist)
        list1 = [str(i) for i in list1]

        list3 = list()
        for x in list1:
            if x not in events:
                list3.append(x)

        context["object_list"] = {
            "vanum": str(len(list3)),
            "total": str(eventsnum),
            "push": push,
        }

        return context


index_view = IndexView.as_view()


class pushDHISView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "pages/dhis.html"
    permission_required = "dhis_manager.change_dhisstatus"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        env = environ.Env()
        # DHIS2 VARIABLES
        DHIS2_USER = env("DHIS2_USER")
        DHIS2_PASS = env("DHIS2_PASS")

        cmd = Command()
        auth = (DHIS2_USER, DHIS2_PASS)

        va_in_dhis2 = cmd.getPushedVA("sv91bCroFFx", auth)
        eventsnum = len(va_in_dhis2)
        dhisdata = [int(i) for i in va_in_dhis2]

        vadata = (
            VerbalAutopsy.objects.filter(causes__isnull=False, dhisva__isnull=True)
            .exclude(id__in=dhisdata)
            .count()
        )
        if vadata > 0:
            numPushed, numTotal, status = cmd.handle()
        else:
            cmd.syncDHISStatus()
            status = "Nothing to push"
        btnpush = "OK"

        if status == "SUCCESS":
            txt = (
                "successfully posted "
                + str(numPushed)
                + " out of "
                + str(numTotal)
                + " records"
            )
        else:
            txt = "Nothing to Post!"

        context["object_list"] = {
            "txt": txt,
            "vanum": str(vadata),
            "btnpush": btnpush,
            "total": eventsnum,
        }

        return context


push_DHISView = pushDHISView.as_view()
