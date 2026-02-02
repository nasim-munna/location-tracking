from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    LoginView,
    RegisterView,
    UserViewSet,
    DivisionListAPIView,
    DivisionEmployeeAPIView,
    SaveFCMTokenAPIView,
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')

urlpatterns = [
    # ViewSet routes
    path("", include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Division APIs
    path("divisions/",DivisionListAPIView.as_view(),name="division-list"),
    path("divisions/<int:division_id>/employees/",DivisionEmployeeAPIView.as_view(),name="division-employees"
    ),
    path("fcm-token/",SaveFCMTokenAPIView.as_view(),name="save-fcm-token"),
]
