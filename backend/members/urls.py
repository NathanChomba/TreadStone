from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view()),
    path("login/", views.LoginView.as_view()),
    path("logout/", views.LogoutView.as_view()),
    path("me/", views.MeView.as_view()),
    path("dashboard/", views.DashboardView.as_view()),
    path("password/", views.ChangePasswordView.as_view()),
    path("wallets/", views.WalletListView.as_view()),
    path("wallets/<int:pk>/default/", views.WalletDefaultView.as_view()),
    path("wallets/<int:pk>/", views.WalletDeleteView.as_view()),
    path("notifications/", views.NotificationListView.as_view()),
    path("notifications/read/", views.NotificationReadView.as_view()),
]
