from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from loans.views import LoanLimitView, LoanViewSet
from savings.views import ContributionViewSet, SavingsGroupViewSet

router = DefaultRouter()
router.register("groups", SavingsGroupViewSet, basename="group")
router.register("contributions", ContributionViewSet, basename="contribution")
router.register("loans", LoanViewSet, basename="loan")

admin.site.site_header = "Treadstone administration"
admin.site.site_title = "Treadstone"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("members.urls")),
    path("api/metals/", include("metals.urls")),
    path("api/payouts/", include("payouts.urls")),
    path("api/loans/limit/", LoanLimitView.as_view()),
    path("api/", include(router.urls)),
]
