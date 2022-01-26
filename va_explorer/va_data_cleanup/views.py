from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    DeleteView,
    ListView,
)

from .models import DataCleanup
from ..va_data_management.models import VerbalAutopsy
from ..utils.mixins import CustomAuthMixin

User = get_user_model()


class DataCleanupIndexView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_data_cleanup.view_datacleanup"
    model = DataCleanup
    paginate_by = 10
    template_name = 'va_data_cleanup/index.html'

    def get_queryset(self):
        # Restrict to VAs this user can access and prefetch related for performance
        queryset = self.request.user.verbal_autopsies().prefetch_related("location").order_by("id").filter(duplicate=True)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
