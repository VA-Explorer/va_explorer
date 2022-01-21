from django.shortcuts import render

from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    ListView,
)

from .models import DataCleanup
from ..utils.mixins import CustomAuthMixin

User = get_user_model()


class DataCleanupIndexView(CustomAuthMixin, PermissionRequiredMixin, ListView):
    permission_required = "va_data_cleanup.view_datacleanup"
    model = DataCleanup
    paginate_by = 10
    template_name = 'va_data_cleanup/index.html'

    def get_queryset(self):
        # Restrict to VAs this user can access and prefetch related for performance
        queryset = self.request.user.verbal_autopsies().prefetch_related("location", "causes", "coding_issues").order_by("id")

        return queryset


data_cleanup_index_view = DataCleanupIndexView.as_view()
