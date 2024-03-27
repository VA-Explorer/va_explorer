from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import CharField
from django.db.models import Value as V
from django.db.models.functions import Concat
from django.http import Http404, HttpResponse
from django.views.generic import ListView, View

from ..utils.file_io import download_list_as_csv, download_queryset_as_csv
from ..utils.mixins import CustomAuthMixin
from ..va_data_management.models import (
    VerbalAutopsy,
    questions_to_autodetect_duplicates,
)
from ..va_data_management.utils.date_parsing import parse_date
from .models import DataCleanup

User = get_user_model()


class DataCleanupIndexView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_data_cleanup.view_datacleanup"
    model = DataCleanup
    paginate_by = 10
    template_name = "va_data_cleanup/index.html"

    def get_queryset(self):
        queryset = (
            self.request.user.verbal_autopsies()
            .prefetch_related("location", "causes", "coding_issues")
            .annotate(
                deceased=Concat("Id10017", V(" "), "Id10018", output_field=CharField())
            )
            .order_by("id")
            .filter(duplicate=True)
        )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["total_duplicate_records"] = (
            self.request.user.verbal_autopsies().filter(duplicate=True).count()
        )
        context["va_data_cleanup"] = True

        context["object_list"] = [
            {
                "id": va.id,
                "interviewer": va.Id10010,
                "interviewed": parse_date(va.Id10012),
                "dod": parse_date(va.Id10023) if (va.Id10023 != "dk") else "Unknown",
                "facility": va.location.name if va.location else "Not Provided",
                "deceased": va.deceased,
                "cause": (
                    va.causes.all()[0].cause
                    if len(va.causes.all()) > 0
                    else "Not Coded"
                ),
                "warnings": len(
                    [
                        issue
                        for issue in va.coding_issues.all()
                        if issue.severity == "warning"
                    ]
                ),
                "errors": len(
                    [
                        issue
                        for issue in va.coding_issues.all()
                        if issue.severity == "error"
                    ]
                ),
            }
            for va in context["object_list"]
        ]

        return context


data_cleanup_index_view = DataCleanupIndexView.as_view()


class DownloadIndividual(View):
    def get(self, request, **kwargs):
        pk = kwargs.pop("pk", None)

        if not pk or not request.user.has_perm("va_data_cleanup.download"):
            raise PermissionDenied

        if pk:
            try:
                va = VerbalAutopsy.objects.get(pk=pk)
                # Check that the VA passed in is indeed a duplicate and is a VA
                # that the user can access. Guards against a user manually
                # passing in an arbitrary VA ID to va_data_cleanup/download/:id
                if (
                    not self.request.user.verbal_autopsies()
                    .filter(id=va.id, duplicate=True)
                    .exists()
                ):
                    raise PermissionDenied

                query_set = (
                    self.request.user.verbal_autopsies()
                    .filter(unique_va_identifier=va.unique_va_identifier)
                    .order_by("created")
                )

                response = download_queryset_as_csv(
                    query_set, "duplicate_vas_matching_individual", "data_cleanup/"
                )

                return HttpResponse(response, content_type="text/csv")
            # Encountered if user manually passes in a pk to URL that does not exist or
            # User manually passes in the pk of a soft-deleted VA
            except VerbalAutopsy.DoesNotExist as err:
                raise Http404("This Verbal Autopsy does not exist.") from err


download = DownloadIndividual.as_view()


class DownloadAll(View):
    def get(self, request, **kwargs):
        if not request.user.has_perm("va_data_cleanup.bulk_download"):
            raise PermissionDenied

        query_set = (
            self.request.user.verbal_autopsies()
            .filter(duplicate=True)
            .order_by("unique_va_identifier")
        )

        data = download_queryset_as_csv(query_set, "all_duplicates", "data_cleanup/")

        return HttpResponse(data, content_type="text/csv")


download_all = DownloadAll.as_view()


# Download the questions used to autodetect duplicate VAs as a csv
class DownloadQuestions(View):
    def get(self, request, **kwargs):
        if not request.user.has_perm("va_data_cleanup.view_datacleanup"):
            raise PermissionDenied

        data = download_list_as_csv(
            questions_to_autodetect_duplicates(),
            "questions_to_autodetect_duplicates",
            "data_cleanup/",
        )
        return HttpResponse(data, content_type="text/csv")


download_questions = DownloadQuestions.as_view()
