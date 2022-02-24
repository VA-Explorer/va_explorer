from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, ListView, RedirectView
from django.views.generic.detail import SingleObjectMixin
from django.db.models import F, Q, Count, Value as V
from django.db.models.functions import Concat

import logging

from config.celery_app import app
from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.filters import VAFilter
from va_explorer.va_data_management.forms import VerbalAutopsyForm
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.tasks import run_coding_algorithms
from va_explorer.va_data_management.utils.loading import get_va_summary_stats
from va_explorer.va_logs.logging_utils import write_va_log
from va_explorer.va_data_management.utils.validate import validate_vas_for_dashboard
from va_explorer.va_data_management.utils.date_parsing import parse_date, get_submissiondate

import time
import re


LOGGER = logging.getLogger("event_logger")

class Index(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_data_management.view_verbalautopsy"
    template_name = 'va_data_management/index.html'
    paginate_by = 15

    def get_queryset(self):

        # Restrict to VAs this user can access and prefetch related for performance
        ti=time.time(); queryset = (self.request.user.verbal_autopsies()\
                    .select_related("location")\
                    .select_related("causes")\
                    .select_related("coding_issues")\
                    .annotate(deceased = Concat('Id10017', V(' '), 'Id10018'))
                    .values("id",
                            "location__name",
                            "causes__cause",
                            "Id10023",
                            "Id10010",
                            "submissiondate",
                            "deceased",
                            errors=Count(F("coding_issues"), filter=Q(coding_issues__severity="error")),
                            warnings=Count(F("coding_issues"), filter=Q(coding_issues__severity="warning")))); print(f"total time: {time.time()-ti} secs")

        # sort by chosen field (default is VA ID)
        # get raw sort key (includes direction)
        sort_key_raw = self.request.GET.get("order_by", "id")
        # strip out direction and map to va field
        sort_key = sort_key_raw.lstrip("-")
        sort_key_to_field = {
            'id': 'id',
            'interviewer': 'Id10010',
            'dod': 'Id10023',
            'facility': 'location__name',
            'cause': 'causes__cause',
            'submitted': 'submissiondate',
            'deceased': 'deceased'
        }
        sort_field = sort_key_to_field.get(sort_key, sort_key)
        # add sort direction
        if sort_key_raw.startswith("-") and not sort_field.startswith("-"):
            sort_field = "-" + sort_field
        queryset = queryset.order_by(sort_field)

        self.filterset = VAFilter(data=self.request.GET or None, queryset=queryset)
        if self.request.user.is_fieldworker():
            del self.filterset.form.fields['interviewer']

        # Don't allow search based on fields the user can't see anyway
        if not self.request.user.can_view_pii:
            del self.filterset.form.fields['deceased']
            del self.filterset.form.fields['start_date']
            del self.filterset.form.fields['end_date']

        query_dict = self.request.GET.dict()
        query_keys = [k for k in query_dict if k != 'csrfmiddlewaretoken']
        if len(query_keys) > 0:
            query = ', '.join([f"{k}: {query_dict[k]}" for k in query_keys if query_dict[k] != ""])
            write_va_log(LOGGER, f"[data_mgnt] Queried VAs for: {query}", self.request)

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filterset"] = self.filterset

        # ids for va download
        download_ids = [str(i) for i in self.filterset.qs.values_list("id", flat=True)]
        if len(download_ids) > 0:
            context["download_url"] = reverse('va_export:va_api') + '?ids=' + ','.join(download_ids) # self.request.get_host() + 
        else:
            # filter returned no results - render button useless
            context["download_url"] = ""

        ti = time.time()
        context['object_list'] = [{
            "id": va["id"],
            "deceased": va["deceased"],
            "interviewer": va["Id10010"],
            "submitted":  va["submissiondate"], #get_submissiondate(va, empty_string="Unknown", parse=True), #django stores the date in yyyy-mm-dd
            "dod":  parse_date(va["Id10023"]) if (va["Id10023"] != 'dk') else "Unknown",
            "facility": va["location__name"], #va.location.name if va.location else "",
            "cause": va["causes__cause"],  #va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
            "warnings": va["warnings"], #len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
            "errors": va["errors"]# len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
        } for va in context['object_list']]

        context.update(get_va_summary_stats(self.filterset.qs))
        print(f"total time to format display VAs: {time.time() - ti} secs")

        return context




# Mixin just for the individual verbal autopsy data management views to restrict access based on user
class AccessRestrictionMixin(SingleObjectMixin):
    def get_queryset(self):
        # Restrict to VAs this user can access
        return self.request.user.verbal_autopsies()


class Show(CustomAuthMixin, AccessRestrictionMixin, PermissionRequiredMixin, DetailView):
    permission_required = "va_data_management.view_verbalautopsy"
    template_name = 'va_data_management/show.html'
    model = VerbalAutopsy
    pk_url_kwarg = 'id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['id'] = self.object.id
        context['form'] = VerbalAutopsyForm(None, instance=self.object)

        coding_issues = self.object.coding_issues.all()
        context['warnings'], context['algo_warnings'] = self.filter_warnings([issue for issue in coding_issues if issue.severity == 'warning'])
        context['errors'] = [issue for issue in coding_issues if issue.severity == 'error']


        # TODO: date in diff info should be formatted in local time
        history = self.object.history.all().reverse()
        history_pairs = zip(history, history[1:])
        context['diffs'] = [new.diff_against(old) for (old, new) in history_pairs]
        
        # log view record event
        write_va_log(LOGGER, f"[data_mgnt] Clicked view record for va {self.object.id}", self.request)

        return context
    
    # this function uses regex to filters out user warnings and algorithm warnings based on an observed pattern 
    @staticmethod
    def filter_warnings(warnings):
        user_warnings = []
        algo_warnings = []
        for warning in warnings:
            if re.search("^W\d{6}[-]",str(warning)):
                algo_warnings.append(warning)
            else:
                user_warnings.append(warning)
        return user_warnings, algo_warnings



class Edit(CustomAuthMixin, PermissionRequiredMixin, AccessRestrictionMixin, SuccessMessageMixin, UpdateView):
    permission_required = "va_data_management.change_verbalautopsy"
    template_name = 'va_data_management/edit.html'
    form_class = VerbalAutopsyForm
    model = VerbalAutopsy
    pk_url_kwarg = 'id'
    success_message = "Verbal Autopsy successfully updated!"

    def get_success_url(self):
        # update the validation errors
        validate_vas_for_dashboard([self.object])
        write_va_log(LOGGER, f"[data_mgnt] successfully saved changes to VA {self.object.id}", self.request)
        return reverse('va_data_management:show', kwargs={'id': self.object.id})

    def get_form_kwargs(self):
        # Tell form to include PII fields if user is able.
        kwargs = super().get_form_kwargs()
        kwargs['include_pii'] = self.request.user.can_view_pii
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['id'] = self.object.id
        # log edit event
        write_va_log(LOGGER, f"[data_mgnt] Clicked edit record for va {context['id']}", self.request)
        return context


class Reset(CustomAuthMixin, PermissionRequiredMixin, AccessRestrictionMixin, DetailView):
    permission_required = "va_data_management.change_verbalautopsy"
    model = VerbalAutopsy
    pk_url_kwarg = 'id'
    success_message = "Verbal Autopsy changes successfully reverted to original!"

    def render_to_response(self, context):
        earliest = self.object.history.earliest()
        latest = self.object.history.latest()
        if earliest and len(latest.diff_against(earliest).changes) > 0:
            earliest.instance.save()
            # update the validation errors
            validate_vas_for_dashboard([earliest])
        # log reset action
        messages.success(self.request, self.success_message)
        write_va_log(LOGGER, f"[data_mgnt] Reset data for va {self.object.id}", self.request)
        return redirect('va_data_management:show', id=self.object.id)


class RevertLatest(CustomAuthMixin, PermissionRequiredMixin, AccessRestrictionMixin, DetailView):
    permission_required = "va_data_management.change_verbalautopsy"
    model = VerbalAutopsy
    pk_url_kwarg = 'id'
    success_message = "Verbal Autopsy changes successfully reverted to previous!"

    def render_to_response(self, context):
        # TODO: Should record automatically be recoded?
        if self.object.history.count() > 1:
            previous = self.object.history.all()[1]
            latest = self.object.history.latest()
            if len(latest.diff_against(previous).changes) > 0:
                previous.instance.save()
                # update the validation errors
                validate_vas_for_dashboard([previous])
        messages.success(self.request, self.success_message)
        # log revert changes action
        write_va_log(LOGGER, f"[data_mgnt] Reverted changes for va {self.object.id}", self.request)
        return redirect('va_data_management:show', id=self.object.id)


class RunCodingAlgorithm(RedirectView, PermissionRequiredMixin):
    permission_required = "va_data_management.change_verbalautopsy"
    pattern_name = 'home:index'

    def post(self, request, *args, **kwargs):
        run_coding_algorithms.apply_async()
        messages.success(request, f"Coding algorithm process has started in the background.")
        write_va_log(LOGGER, "ran coding algorithm", self.request)
        return super().post(request, *args, **kwargs)
