from django.urls import path

from va_explorer.dhis_manager.views import (
index_view,
push_DHISView
)

app_name = "dhis_manager"

urlpatterns = [
    path('', view=index_view, name='dhishome'),
    path('dhisresults/', view=push_DHISView, name='dhisrecords')
]
