import logging
import os

from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import TemplateView
from requests import RequestException

from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.management.commands.run_dhis import Command
from va_explorer.va_data_management.models import VerbalAutopsy

DHIS_USER = os.environ.get("DHIS_USER", "admin")
DHIS_PASS = os.environ.get("DHIS_PASS", "district")
LOGGER = logging.getLogger()


class IndexView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "pages/dhis.html"
    permission_required = "dhis_manager.change_dhisstatus"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        push = "notyet"

        try:
            cmd = Command()
            auth = (DHIS_USER, DHIS_PASS)
            events_num = cmd.get_events_values("sv91bCroFFx", auth)
            cmd.sync_dhis_status()
            events = cmd.get_pushed_va("sv91bCroFFx", auth)

            va_list = VerbalAutopsy.objects.filter(
                causes__isnull=False, dhisva__isnull=True
            ).values_list("id", flat=True)
            list1 = list(va_list)
            list1 = [str(i) for i in list1]

            list3 = []
            for x in list1:
                if x not in events:
                    list3.append(x)

            context["object_list"] = {
                "vanum": str(len(list3)),
                "total": str(events_num),
                "push": push,
            }

        except RequestException as err:
            LOGGER.error(err)
            messages.add_message(
                self.request,
                messages.ERROR,
                "Unable to connect to DHIS2. Check \
                    the DHIS instance or your admin's configuration and try again.",
            )
            context["object_list"] = {
                "vanum": "?",
                "total": "?",
                "push": "?",
            }

        return context


index_view = IndexView.as_view()


class PushDHISView(CustomAuthMixin, PermissionRequiredMixin, TemplateView):
    template_name = "pages/dhis.html"
    permission_required = "dhis_manager.change_dhisstatus"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cmd = Command()
        auth = (DHIS_USER, DHIS_PASS)

        try:
            va_in_dhis = cmd.get_pushed_va("sv91bCroFFx", auth)
            events_num = len(va_in_dhis)
            dhis_data = [int(i) for i in va_in_dhis]

            va_data = (
                VerbalAutopsy.objects.filter(causes__isnull=False, dhisva__isnull=True)
                .exclude(id__in=dhis_data)
                .count()
            )
            if va_data > 0:
                num_pushed, num_total, status = cmd.handle()
            else:
                cmd.sync_dhis_status()
                status = "Nothing to push"
            btn_push = "OK"

            if status == "SUCCESS":
                txt = (
                    "successfully posted "
                    + str(num_pushed)
                    + " out of "
                    + str(num_total)
                    + " records"
                )
            else:
                txt = "Nothing to Post!"

            context["object_list"] = {
                "txt": txt,
                "vanum": str(va_data),
                "btnpush": btn_push,
                "total": events_num,
            }

        except RequestException as err:
            LOGGER.error(err)
            messages.add_message(
                self.request,
                messages.ERROR,
                "Unable to connect to DHIS2. Check \
                    the DHIS instance or your admin's configuration and try again.",
            )
            context["object_list"] = {
                "vanum": "?",
                "total": "?",
                "push": "?",
            }

        return context


push_dhis_view = PushDHISView.as_view()
