from django.http import JsonResponse
from django.views.generic import TemplateView, View

from va_explorer.home.va_trends import get_trends_data
from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.utils.loading import get_va_summary_stats


class Index(CustomAuthMixin, TemplateView):
    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        # TODO: interviewers should only see their own data
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update(get_va_summary_stats(user.verbal_autopsies()))

        context["locations"] = "All Regions"
        if user.location_restrictions.count() > 0:
            context["locations"] = ", ".join(
                [location.name for location in user.location_restrictions.all()]
            )

        return context


class Trends(CustomAuthMixin, View):
    def get(self, request, *args, **kwargs):
        (
            va_table,
            graphs,
            issue_list,
            indeterminate_cod_list,
            additional_issues,
            additional_indeterminate_cods,
        ) = get_trends_data(request.user)

        return JsonResponse(
            {
                "vaTable": va_table,
                "graphs": graphs,
                "issueList": issue_list,
                "indeterminateCodList": indeterminate_cod_list,
                "additionalIssues": additional_issues,
                "additionalIndeterminateCods": additional_indeterminate_cods,
                "isFieldWorker": request.user.is_fieldworker(),
            }
        )


trends_endpoint_view = Trends.as_view()


class About(CustomAuthMixin, TemplateView):
    template_name = "home/about.html"
