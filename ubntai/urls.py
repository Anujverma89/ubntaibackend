from . import views
from django.urls import path

urlpatterns=[
    path("getpastqueries",views.getpastqueries),
    path("savepastqueries",views.savepastqueries),
    path("deletepastqueries",views.deletepastqueries),
    path("getanswer",views.getAnswer),
    path("troubleshoot", views.troubleShoot),
    path("adderrorreport",views.add_error_report),
    path("addapplicationinfo", views.add_application_info),

]