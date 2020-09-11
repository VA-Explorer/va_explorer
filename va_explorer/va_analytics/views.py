from django.views.generic import TemplateView


class DashboardView(TemplateView):
    template_name = "va_analytics/dashboard.html"


dashboard_view = DashboardView.as_view()
