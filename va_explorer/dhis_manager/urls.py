from django.urls import path

from . import views

app_name = "dhis_manager"

urlpatterns = [
    path('', views.index, name='dhishome'),
    path('dhisresults/', views.pushDHIS, name='dhisrecords')
]
