from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db import models

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from locations.throttles import GPSThrottle
from users.permissions import IsEmployee, IsAdmin, IsSuperAdmin
from users.models import EmployeeProfile, User

from drf_spectacular.utils import extend_schema, OpenApiTypes
from rest_framework import serializers # ensure serializers is imported

from .models import (
    LocationLog,
    Office,
    Attendance,
    GeofenceEvent,
)
from .serializers import (
    LocationCreateSerializer,
    LocationReadSerializer,
    AttendanceSerializer,
    AttendanceReportSerializer,
    GeofenceEventSerializer
)
from .utils import calculate_distance


# ======================================================
# SEND LOCATION (EMPLOYEE)
# ======================================================
# locations/views.py

class SendLocationAPIView(CreateAPIView):
    serializer_class = LocationCreateSerializer
    permission_classes = [IsEmployee]

    def perform_create(self, serializer):
        user = self.request.user
        location = serializer.save(user=user)
        
        # ১. ডাটাবেসে সেভ হওয়ার পর WebSocket এ অ্যাডমিনকে জানানো
        channel_layer = get_channel_layer()
        division_id = user.profile.division_id
        
        if division_id:
            async_to_sync(channel_layer.group_send)(
                f"division_{division_id}",
                {
                    "type": "broadcast_location", # consumers.py এর মেথড নামের সাথে মিল থাকতে হবে
                    "data": {
                        "user_id": str(user.id),
                        "name": user.full_name,
                        "lat": location.latitude,
                        "lng": location.longitude,
                        "time": str(location.recorded_at)
                    }
                }
            )

# ======================================================
# EMPLOYEE LOCATION HISTORY
# ======================================================
class MyLocationHistoryAPIView(ListAPIView):
    serializer_class = LocationReadSerializer

    def get_queryset(self):
        return LocationLog.objects.filter(
            user=self.request.user
        ).order_by("-recorded_at")


# ======================================================
# ADMIN / SUPERADMIN USER LOCATIONS
# ======================================================
class UserLocationAPIView(ListAPIView):
    permission_classes = [IsAdmin, IsSuperAdmin]
    serializer_class = LocationReadSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        request_user = self.request.user

        if request_user.role == "ADMIN":
            if not EmployeeProfile.objects.filter(
                user_id=user_id,
                admin=request_user,
            ).exists():
                raise PermissionDenied("This employee is not assigned to you")

        qs = LocationLog.objects.filter(user_id=user_id)

        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        if start:
            start_dt = parse_datetime(start)
            if start_dt:
                qs = qs.filter(recorded_at__gte=start_dt)

        if end:
            end_dt = parse_datetime(end)
            if end_dt:
                qs = qs.filter(recorded_at__lte=end_dt)

        return qs.order_by("-recorded_at")


# ======================================================
# LATEST LOCATION (MAP MARKER)
# ======================================================
class LatestLocationAPIView(APIView):
    permission_classes = [IsAdmin, IsSuperAdmin]

    def get(self, request, user_id):
        loc = LocationLog.objects.filter(
            user_id=user_id
        ).order_by("-recorded_at").first()

        if not loc:
            return Response({})

        return Response({
            "lat": loc.latitude,
            "lng": loc.longitude,
            "time": loc.recorded_at,
        })


# ======================================================
# ROUTE / POLYLINE
# ======================================================
class RouteAPIView(APIView):
    permission_classes = [IsAdmin, IsSuperAdmin]

    def get(self, request, user_id):
        locations = LocationLog.objects.filter(
            user_id=user_id
        ).order_by("recorded_at")

        return Response([
            {"lat": l.latitude, "lng": l.longitude}
            for l in locations
        ])


# ======================================================
# ATTENDANCE (EMPLOYEE)
# ======================================================
class MyAttendanceAPIView(ListAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        return Attendance.objects.filter(
            user=self.request.user
        ).order_by("-date")


# ======================================================
# ATTENDANCE (ADMIN / SUPERADMIN)
# ======================================================
class UserAttendanceAPIView(ListAPIView):
    permission_classes = [IsAdmin, IsSuperAdmin]
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        request_user = self.request.user

        if request_user.role == "ADMIN":
            if not EmployeeProfile.objects.filter(
                user_id=user_id,
                admin=request_user,
            ).exists():
                raise PermissionDenied("This employee is not assigned to you")

        return Attendance.objects.filter(
            user_id=user_id
        ).order_by("-date")


# ======================================================
# MONTHLY REPORTS
# ======================================================
class MyMonthlyAttendanceAPIView(ListAPIView):
    serializer_class = AttendanceReportSerializer

    def get_queryset(self):
        month_param = self.request.query_params.get("month")  # YYYY-MM
        if not month_param:
            return Attendance.objects.none()

        try:
            year, month_val = map(int, month_param.split("-"))
        except (ValueError, TypeError):
            return Attendance.objects.none()

        return Attendance.objects.filter(
            user=self.request.user,
            date__year=year,
            date__month=month_val,
        ).order_by("date")


class EmployeeMonthlyAttendanceAPIView(ListAPIView):
    permission_classes = [IsAdmin, IsSuperAdmin]
    serializer_class = AttendanceReportSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        request_user = self.request.user

        if request_user.role == "ADMIN":
            if not EmployeeProfile.objects.filter(
                user_id=user_id,
                admin=request_user,
            ).exists():
                raise PermissionDenied("Not your employee")

        month_param = self.request.query_params.get("month")
        if not month_param:
            return Attendance.objects.none()

        try:
            year, month_val = map(int, month_param.split("-"))
        except (ValueError, TypeError):
            return Attendance.objects.none()

        return Attendance.objects.filter(
            user_id=user_id,
            date__year=year,
            date__month=month_val,
        ).order_by("date")


# ======================================================
# ADMIN DASHBOARD SUMMARY
# ======================================================

class AdminAttendanceSummaryAPIView(APIView):
    permission_classes = [IsAdmin, IsSuperAdmin]

    @extend_schema(
        responses={
            200: OpenApiTypes.OBJECT  # Tells the tool it returns a JSON object
        },
        description="Returns daily attendance summary: counts for present, absent, and late employees."
    )
    def get(self, request):
        user = request.user
        today = timezone.now().date()

        qs = Attendance.objects.filter(date=today)

        if user.role == "ADMIN":
            qs = qs.filter(user__profile__admin=user)

        present = qs.filter(check_in__isnull=False).count()
        absent = qs.filter(check_in__isnull=True).count()
        late = qs.filter(
            check_in__time__gt=models.F("office__work_start_time")
        ).count()

        return Response({
            "present": present,
            "absent": absent,
            "late": late,
        })


# ======================================================
# DIVISION LIVE LOCATION (MAP LOAD)
# ======================================================
# Inside locations/views.py

class DivisionLiveLocationAPIView(APIView):
    permission_classes = [IsAdmin, IsSuperAdmin]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT}, 
        description="Returns a list of the latest locations for all employees in a specific division."
    )
    def get(self, request, division_id):
        user = request.user

        # Restrict Admins to their own employees
        employees_qs = User.objects.filter(
            profile__division_id=division_id,
            role="EMPLOYEE",
        )

        if user.role == "ADMIN":
            employees_qs = employees_qs.filter(profile__admin=user)

        data = []
        for emp in employees_qs:
            loc = (
                LocationLog.objects.filter(user=emp)
                .order_by("-recorded_at")
                .first()
            )

            if not loc:
                continue

            data.append({
                "user_id": str(emp.id),
                "name": getattr(emp, "full_name", emp.email),
                "lat": loc.latitude,
                "lng": loc.longitude,
                "time": loc.recorded_at.isoformat(),
            })

        return Response(data)

class GeofenceEventAPIView(ListAPIView):
    serializer_class = GeofenceEventSerializer
    permission_classes = [IsAdmin, IsSuperAdmin]

    def get_queryset(self):
        qs = GeofenceEvent.objects.select_related("user")

        division_id = self.request.query_params.get("division")
        if division_id:
            qs = qs.filter(user__profile__division_id=division_id)

        return qs.order_by("-occurred_at")
