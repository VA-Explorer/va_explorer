from django.views.generic import TemplateView
from django.db.models import Count
from django.db.models.functions import TruncMonth
from va_explorer.utils.mixins import CustomAuthMixin
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np

# TODO: We're using plotly here since it's already included in the project, but there may be slimmer options
import plotly.offline as opy
import plotly.graph_objs as go

# Simple helper function for creating the plotly graphs used on the home page
def graph(x, y):
    figure = go.Figure(data=go.Scatter(x=x, y=y))
    figure.update_layout(autosize=False, width=300, height=100, margin=dict(l=0, r=0, t=0, b=0, pad=0))
    config = {'displayModeBar': False}
    return opy.plot(figure, auto_open=False, output_type='div', config=config)

class Index(CustomAuthMixin, TemplateView):

    template_name = "home/index.html"

    def get_context_data(self, **kwargs):
        # TODO: interviewers should only see their own data
        context = super().get_context_data(**kwargs)

        user = self.request.user
        user_vas = user.verbal_autopsies()
        location_restrictions = user.location_restrictions
        today = date.today()

        if location_restrictions.count() > 0:
            context['locations'] = ', '.join([location.name for location in location_restrictions.all()])
        else:
            context['locations'] = 'All Regions'

        # Load the VAs that are collected over various periods of time
        # TODO: We're using date imported, but might be more appropriate to use date collected? If updating
        # this, look for all references to 'created'
        vas_24_hours = user_vas.filter(created__gte=today)
        vas_1_week = user_vas.filter(created__gte=today - timedelta(days=7))
        vas_1_month = user_vas.filter(created__gte=today - relativedelta(months=1))
        vas_overall = user_vas.order_by('id')

        # VAs collected in the past 24 hours, 1 week, and 1 month
        context['vas_collected_24_hours'] = vas_24_hours.count()
        context['vas_collected_1_week'] = vas_1_week.count()
        context['vas_collected_1_month'] = vas_1_month.count()
        context['vas_collected_overall'] = vas_overall.count()
        # VAs successfully coded in the past 24 hours, 1 week, and 1 month
        context['vas_coded_24_hours'] = vas_24_hours.filter(causes__isnull=False).count()
        context['vas_coded_1_week'] = vas_1_week.filter(causes__isnull=False).count()
        context['vas_coded_1_month'] = vas_1_month.filter(causes__isnull=False).count()
        context['vas_coded_overall'] = vas_overall.filter(causes__isnull=False).count()
        # VAs not able to be coded in the past 24 hours, 1 week, and 1 month
        context['vas_uncoded_24_hours'] = context['vas_collected_24_hours'] - context['vas_coded_24_hours']
        context['vas_uncoded_1_week'] = context['vas_collected_1_week'] - context['vas_coded_1_week']
        context['vas_uncoded_1_month'] = context['vas_collected_1_month'] - context['vas_coded_1_month']
        context['vas_uncoded_overall'] = context['vas_collected_overall'] - context['vas_coded_overall']

        # Graphs of the past 12 months, not including this month (including the current month will almost
        # always show the month with artificially low numbers)
        start_month = date(today.year - 1, today.month, 1)
        months = [start_month + relativedelta(months=i) for i in range(12)]
        x = [month.strftime('%b') for month in months]

        # Collected; this query groups by month (cast to a date from a datetime) and returns the counts by month
        collected_counts = user_vas.filter(created__gte=start_month).annotate(month=TruncMonth('created')).values('month').annotate(count=Count('*'))
        collected_by_month = {entry['month'].date():entry['count'] for entry in collected_counts}
        y_collected = [collected_by_month.get(month, 0) for month in months]
        context['graph_collected'] = graph(x, y_collected)

        # Coded; same query as above, just filtered by whether the va has been coded
        coded_counts = user_vas.filter(created__gte=start_month, causes__isnull=False).annotate(month=TruncMonth('created')).values('month').annotate(count=Count('*'))
        coded_by_month = {entry['month'].date():entry['count'] for entry in coded_counts}
        y_coded = [coded_by_month.get(month, 0) for month in months]
        context['graph_coded'] = graph(x, y_coded)

        # Uncoded; just take the difference between the two previous queries
        context['graph_uncoded'] = graph(x, np.subtract(y_collected, y_coded))

        # List the VAs that need attention; requesting certain fields and prefetching makes this more efficient
        vas_to_address = vas_overall.only('id', 'location_id', 'Id10007', 'Id10023').filter(causes__isnull=True).prefetch_related("causes", "coding_issues", "location")[:10]
        context['issue_list'] = [{
            "id": va.id,
            "name": va.Id10007,
            "date":  va.Id10023 if (va.Id10023 != 'dk') else "Unknown", #django stores the date in yyyy-mm-dd
            "facility": va.location.name if va.location else "",
            "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
            "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
            "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
        } for va in vas_to_address]

        # If there are more than 10 show a link to where the rest can be seen
        context['additional_issues'] = max(context['vas_uncoded_overall'] - 10, 0)

        return context


class About(CustomAuthMixin, TemplateView):
    template_name = "home/about.html"
