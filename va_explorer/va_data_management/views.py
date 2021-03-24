from django.contrib import messages
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import DetailView, UpdateView, ListView, RedirectView
from django.views.generic.detail import SingleObjectMixin
from datetime import datetime

from config.celery_app import app
from va_explorer.utils.mixins import CustomAuthMixin
from va_explorer.va_data_management.filters import VAFilter
from va_explorer.va_data_management.forms import VerbalAutopsyForm
from va_explorer.va_data_management.models import VerbalAutopsy
from va_explorer.va_data_management.tasks import run_coding_algorithms
from va_explorer.va_data_management.utils.validate import validate_va_records


class Index(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_data_management.view_verbalautopsy"
    template_name = 'va_data_management/index.html'
    paginate_by = 15

    def get_queryset(self):
        # Restrict to VAs this user can access and prefetch related for performance
        queryset = self.request.user.verbal_autopsies().prefetch_related("location", "causes", "coding_issues").order_by("id")

        # TODO: For now, we are not displaying the filters for the Field Worker on the VA index page,
        # since many do not apply to them. This prevents data passed through the params from being
        # passed to the VAFilter
        if self.request.user.is_fieldworker():
            self.filterset = VAFilter(data=None, queryset=queryset)

        # do the filtering thing
        else:
            self.filterset = VAFilter(data=self.request.GET or None, queryset=queryset)

        return self.filterset.qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["filterset"] = self.filterset
        
        context['object_list'] = [{
            "id": va.id,
            "name": va.Id10007,
            "date": va.Id10023,
            "facility": va.location.name,
            "cause": va.causes.all()[0].cause if len(va.causes.all()) > 0 else "",
            "warnings": len([issue for issue in va.coding_issues.all() if issue.severity == 'warning']),
            "errors": len([issue for issue in va.coding_issues.all() if issue.severity == 'error'])
        } for va in context['object_list']]

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
        context['warnings'] = [issue for issue in coding_issues if issue.severity == 'warning']
        context['errors'] = [issue for issue in coding_issues if issue.severity == 'error']

        # TODO: date in diff info should be formatted in local time
        history = self.object.history.all().reverse()
        history_pairs = zip(history, history[1:])
        context['diffs'] = [new.diff_against(old) for (old, new) in history_pairs]

        return context


class Edit(CustomAuthMixin, PermissionRequiredMixin, AccessRestrictionMixin, SuccessMessageMixin, UpdateView):
    permission_required = "va_data_management.change_verbalautopsy"
    template_name = 'va_data_management/edit.html'
    form_class = VerbalAutopsyForm
    model = VerbalAutopsy
    pk_url_kwarg = 'id'
    success_message = "Verbal Autopsy successfully updated!"

    def get_success_url(self):
        # update the validation errors
        validate_va_records([self.object])
        return reverse('va_data_management:show', kwargs={'id': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['id'] = self.object.id
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
            validate_va_records([earliest])
        messages.success(self.request, self.success_message)
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
                validate_va_records([previous])
        messages.success(self.request, self.success_message)
        return redirect('va_data_management:show', id=self.object.id)


class RunCodingAlgorithm(RedirectView, PermissionRequiredMixin):
    permission_required = "va_data_management.change_verbalautopsy"
    pattern_name = 'home:index'

    def post(self, request, *args, **kwargs):
        run_coding_algorithms.apply_async()
        messages.success(request, f"Coding algorithm process has started in the background.")
        return super().post(request, *args, **kwargs)
