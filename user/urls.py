from django.urls import path
from . import views;


urlpatterns=[
    path("",views.blank),
    path("createuser",views.createUser),
    path("updateavatar", views.updateavatar),
    path("getotp",views.sendOTP),
    path("verifyotp",views.verifyOTP),
    path("addsystem",views.createSystemInfo),
    path("getuser",views.getUser),
    path("finduser",views.isUser),
]
