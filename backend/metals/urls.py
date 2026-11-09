from django.urls import path

from . import views

urlpatterns = [
    path("prices/latest/", views.LatestPricesView.as_view()),
    path("prices/", views.PriceHistoryView.as_view()),
    path("ledger/", views.MyLedgerView.as_view()),
    path("history/", views.PriceHistoryRangeView.as_view()),
    path("quote/", views.QuoteView.as_view()),
]
