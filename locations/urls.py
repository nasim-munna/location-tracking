from django.urls import path
from .views import (
    SendLocationAPIView,
    MyLocationHistoryAPIView,
    UserLocationAPIView,
    MyMonthlyAttendanceAPIView,
    EmployeeMonthlyAttendanceAPIView,
    AdminAttendanceSummaryAPIView,
    DivisionLiveLocationAPIView,
)

urlpatterns = [
    path('locations/send/', SendLocationAPIView.as_view()),
    path('locations/me/', MyLocationHistoryAPIView.as_view()),
    path('locations/user/<uuid:user_id>/', UserLocationAPIView.as_view()),
    path("attendance/me/monthly/", MyMonthlyAttendanceAPIView.as_view()),
    path("attendance/user/<uuid:user_id>/monthly/",EmployeeMonthlyAttendanceAPIView.as_view()),
    path("attendance/summary/", AdminAttendanceSummaryAPIView.as_view()),
    path("locations/division/<int:division_id>/live/",DivisionLiveLocationAPIView.as_view()),

]
