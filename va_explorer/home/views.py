from django.views.generic import TemplateView
from django.db.models import Count
from django.db.models.functions import TruncMonth
from va_explorer.utils.mixins import CustomAuthMixin
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
from django.db.models import F
# TODO: We're using plotly here since it's already included in the project, but there may be slimmer options
import plotly.offline as opy
import plotly.graph_objs as go
from va_explorer.va_data_management.utils.loading import get_va_summary_stats
from va_explorer.va_data_management.utils.date_parsing import parse_date, to_dt, get_submissiondates

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
        today = date.today()
        start_month = pd.to_datetime(date(today.year - 1, today.month, 1))
        location_restrictions = user.location_restrictions
        if location_restrictions.count() > 0:
            context['locations'] = ', '.join([location.name for location in location_restrictions.all()])
        else:
            context['locations'] = 'All Regions' 
        # NOTE: using SUBMISSIONDATE to drive stats/views. To change this, change all references to submissiondate
        user_vas = user.verbal_autopsies()
        if user_vas.count() > 0:
            va_df = pd.DataFrame(user_vas\
                .only("id","Id10023","location","Id10011", "submissiondate","created","Id10010", "Id10011") \
                .select_related("location") \
                .select_related("causes") \
                .values("id","Id10023", "created", "Id10011", "submissiondate",\
                    name=F("Id10010"),facility=F("location__name"),cause=F("causes__cause"))
                )
            va_df["date"] = get_submissiondates(va_df)

            # clean date fields - strip timezones from submissiondate and created dates
            va_df["date"] = to_dt(va_df["date"])
            va_df["created"] = to_dt(va_df["created"])
            va_df["Id10023"] = to_dt(va_df["Id10023"])
            va_df["yearmonth"] = va_df["date"].dt.strftime("%Y-%m")
            
            context.update(get_va_summary_stats(user_vas))
            # Load the VAs that are collected over various periods of time
            today = pd.to_datetime(date.today())

            vas_24_hours = va_df[va_df["date"] == today].index
            vas_1_week = va_df[va_df['date'] >= (today - timedelta(days=7))].index
            vas_1_month = va_df[va_df['date'] >= (today - relativedelta(months=1))].index
            vas_overall = va_df.sort_values(by="id").index

            # VAs collected in the past 24 hours, 1 week, and 1 month
            context['vas_collected_24_hours'] = len(vas_24_hours)
            context['vas_collected_1_week'] = len(vas_1_week)
            context['vas_collected_1_month'] = len(vas_1_month)
            context['vas_collected_overall'] = len(vas_overall)
            # VAs successfully coded in the past 24 hours, 1 week, and 1 month        
            context['vas_coded_24_hours'] = va_df.loc[vas_24_hours,:].query("cause == cause").shape[0]
            context['vas_coded_1_week'] = va_df.loc[vas_1_week,:].query("cause == cause").shape[0]
            context['vas_coded_1_month'] = va_df.loc[vas_1_month,:].query("cause == cause").shape[0]
            context['vas_coded_overall'] = va_df.loc[vas_overall,:].query("cause == cause").shape[0]
            # VAs not able to be coded in the past 24 hours, 1 week, and 1 month
            context['vas_uncoded_24_hours'] = context['vas_collected_24_hours'] - context['vas_coded_24_hours']
            context['vas_uncoded_1_week'] = context['vas_collected_1_week'] - context['vas_coded_1_week']
            context['vas_uncoded_1_month'] = context['vas_collected_1_month'] - context['vas_coded_1_month']
            context['vas_uncoded_overall'] = context['vas_collected_overall'] - context['vas_coded_overall']

            # Graphs of the past 12 months, not including this month (current month will almost
            # always show the month with artificially low numbers)
            plot_df = (pd.DataFrame({'month':[start_month + relativedelta(months=i) for i in range(12)]})
                        .assign(month_num = lambda df: df['month'].dt.month)
                )

            months = [start_month + relativedelta(months=i) for i in range(12)]
            x = [month.strftime('%b') for month in months]
            plot_df = pd.DataFrame({'yearmonth': [month.strftime('%Y-%m') for month in months], 'x': x})

            # Collected; total VAs by month
            plot_df = plot_df.merge(va_df.query("date >= @start_month").groupby("yearmonth")["id"].count().rename("y_collected").reset_index(), how="left").fillna(0)
            context['graph_collected'] = graph(plot_df['x'], plot_df['y_collected'])

            # Coded; same query as above, just filtered by whether the va has been coded
            plot_df = plot_df.merge(va_df.query("date >= @start_month & cause==cause").groupby("yearmonth")["id"].count().rename("y_coded").reset_index(), how="left").fillna(0)
            # y_coded = va_df.query().groupby("yearmonth")["id"].count().values
            #y_coded = [coded_by_month.get(month, 0) for month in months]
            context['graph_coded'] = graph(plot_df['x'], plot_df['y_coded'])

            # Uncoded; just take the difference between the two previous queries
            context['graph_uncoded'] = graph(plot_df['x'], (plot_df['y_collected'] - plot_df['y_coded']))

            # List the VAs that need attention; requesting certain fields and prefetching makes this more efficient
            vas_to_address = user_vas.only('id', 'location_id', 'Id10007', 'Id10010', 'Id10017',
                'Id10018', 'submissiondate', 'Id10011', 'Id10023').filter(causes__isnull=True)[:10].prefetch_related("causes", "coding_issues", "location")

            context['issue_list'] = [{
                "id": va.id,
                "deceased": f"{va.Id10017} {va.Id10018}", 
                "interviewer": va.Id10010,
                "submitted":  parse_date(va.submissiondate) if (va.submissiondate != 'dk') else "Unknown", #django stores the date in yyyy-mm-dd
                "dod":  parse_date(va.Id10023) if (va.Id10023 != 'dk') else "Unknown",
                "facility": va.location.name if va.location else "",
                "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
                "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
                "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
            } for va in vas_to_address]

            # If there are more than 10 show a link to where the rest can be seen
            context['additional_issues'] = max(context['vas_uncoded_overall'] - 10, 0)
        # NO VAS FOUND - RETURN EMPTY STATS
        else:
            # empty stats
            for va_type in ['collected', 'coded', 'uncoded']:
                for va_time_period in ['24_hours', '1_week', '1_mont',  'overall']:
                    context[f"vas_{va_type}_{va_time_period}"] = 0
            # empty graphs
            months = [start_month + relativedelta(months=i) for i in range(12)]
            x = [month.strftime('%b') for month in months]
            for va_type in ['collected', 'coded', 'uncoded']: 
                context[f"graph_{va_type}"] = graph(x, np.repeat(0, len(x)))
            context['issue_list'] = []

        return context


class About(CustomAuthMixin, TemplateView):
    template_name = "home/about.html"
