from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse
from django.views.generic import (
    ListView,
    View,
)

from .models import DataCleanup
from ..va_data_management.models import VerbalAutopsy
from ..utils.file_io import download_csv
from ..utils.mixins import CustomAuthMixin

User = get_user_model()


class DataCleanupIndexView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_data_cleanup.view_datacleanup"
    model = DataCleanup
    paginate_by = 10
    template_name = 'va_data_cleanup/index.html'

    def get_queryset(self):
        queryset = self.request.user.verbal_autopsies().order_by("id").filter(duplicate=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_duplicate_records'] =context['object_list'].count()

        context['object_list'] = [{
            "id": va.id,
            "first_name": va.Id10017,
            "surname": va.Id10018,
            "sex": va.Id10019,
            "dob_known": va.Id10020,
            "dob": va.Id10021,
            "dod_known": va.Id10022,
            "dod": va.Id10023 if (va.Id10023 != 'dk') else "Unknown",
        } for va in context['object_list']]

        return context


data_cleanup_index_view = DataCleanupIndexView.as_view()

# TODO: Check that VA is not deleted? User manually creates URL with deleted VA
class DownloadIndividual(View, PermissionRequiredMixin):
    permission_required = "va_data_cleanup.download"

    def get(self, request, **kwargs):
        pk = kwargs.pop("pk", None)

        if pk:
            va = VerbalAutopsy.objects.get(pk=pk)

            query_set = VerbalAutopsy.objects. \
                filter(unique_va_identifier=va.unique_va_identifier, duplicate=True). \
                order_by('created')

            data = download_csv(query_set, "duplicate_vas_matching_individual", "data_cleanup/", 302)

            return HttpResponse(data, content_type='text/csv')


download = DownloadIndividual.as_view()


class DownloadAll(View, PermissionRequiredMixin):
    permission_required = "va_data_cleanup.bulk_download"

    def get(self, request, **kwargs):
        query_set = VerbalAutopsy.objects. \
            filter(duplicate=True). \
            order_by('created')

        data = download_csv(query_set, "all_duplicate_vas", "data_cleanup/", 302)

        return HttpResponse(data, content_type='text/csv')

download_all = DownloadAll.as_view()
