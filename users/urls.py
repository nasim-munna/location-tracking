from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet,
    DivisionListAPIView,
    DivisionEmployeeAPIView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    # ViewSet routes
    path("", include(router.urls)),

    # Division APIs
    path(
        "divisions/",
        DivisionListAPIView.as_view(),
        name="division-list"
    ),
    path(
        "divisions/<int:division_id>/employees/",
        DivisionEmployeeAPIView.as_view(),
        name="division-employees"
    ),
]
