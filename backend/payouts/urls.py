from django.urls import path

from . import views

urlpatterns = [
    path("", views.MyPayoutsView.as_view()),
    path("withdraw/", views.WithdrawView.as_view()),
]
