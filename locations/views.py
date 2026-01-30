from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from locations.throttles import GPSThrottle
from users.permissions import IsEmployee, IsAdmin ,IsSuperAdmin
from rest_framework.exceptions import PermissionDenied
from users.models import EmployeeProfile

from .models import LocationLog, Office, Attendance, User
from .serializers import (
    LocationCreateSerializer,
    LocationReadSerializer,
    AttendanceSerializer,
    AttendanceReportSerializer
)
from .utils import calculate_distance
from locations import models


# -------------------------
# SEND LOCATION (EMPLOYEE)
# -------------------------
class SendLocationAPIView(CreateAPIView):
    serializer_class = LocationCreateSerializer
    permission_classes = [IsEmployee]
    throttle_classes = [GPSThrottle]
    def perform_create(self, serializer):
        # Save location
        location = serializer.save(user=self.request.user)
        user = self.request.user
        vd = serializer.validated_data

        # -------------------------
        # WebSocket broadcast
        # -------------------------
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"location_{user.id}",
                {
                    "type": "send_location",
                    "data": {
                        "lat": vd.get("latitude"),
                        "lng": vd.get("longitude"),
                        "millis": vd.get("millis"),
                    },
                },
            )

        # -------------------------
        # Attendance logic (safe)
        # -------------------------
        office = Office.objects.first()
        if not office:
            return

        try:
            lat = float(vd.get("latitude"))
            lng = float(vd.get("longitude"))
            office_lat = float(office.latitude)
            office_lng = float(office.longitude)
        except (TypeError, ValueError):
            return

        distance = calculate_distance(lat, lng, office_lat, office_lng)
        inside = distance <= office.radius_meters

        now = timezone.now()
        today = now.date()

        attendance, _ = Attendance.objects.get_or_create(
            user=user,
            date=today,
            defaults={"office": office},
        )

        if inside and attendance.check_in is None:
            attendance.check_in = now
            attendance.save()

        if not inside and attendance.check_in and attendance.check_out is None:
            attendance.check_out = now
            attendance.save()


# -------------------------
# EMPLOYEE LOCATION HISTORY
# -------------------------
class MyLocationHistoryAPIView(ListAPIView):
    serializer_class = LocationReadSerializer

    def get_queryset(self):
        return (
            LocationLog.objects
            .filter(user=self.request.user)
            .order_by("-recorded_at")
        )


# -------------------------
# ADMIN / SUPERADMIN USER LOCATIONS
# -------------------------

class UserLocationAPIView(ListAPIView):
    permission_classes = [IsAdmin,IsSuperAdmin]
    serializer_class = LocationReadSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        request_user = self.request.user

        # 🔐 STEP 42: Admin restriction
        if request_user.role == "ADMIN":
            allowed = EmployeeProfile.objects.filter(
                user_id=user_id,
                admin=request_user
            ).exists()

            if not allowed:
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


# -------------------------
# LATEST LOCATION (MAP MARKER)
# -------------------------
class LatestLocationAPIView(APIView):
    permission_classes = [IsAdmin,IsSuperAdmin]

    def get(self, request, user_id):
        loc = (
            LocationLog.objects
            .filter(user_id=user_id)
            .order_by("-recorded_at")
            .first()
        )

        if not loc:
            return Response({})

        return Response({
            "lat": loc.latitude,
            "lng": loc.longitude,
            "time": loc.recorded_at,
        })


# -------------------------
# ROUTE / POLYLINE DATA
# -------------------------
class RouteAPIView(APIView):
    permission_classes = [IsAdmin,IsSuperAdmin]

    def get(self, request, user_id):
        locations = (
            LocationLog.objects
            .filter(user_id=user_id)
            .order_by("recorded_at")
        )

        return Response([
            {"lat": l.latitude, "lng": l.longitude}
            for l in locations
        ])


# -------------------------
# ATTENDANCE (EMPLOYEE)
# -------------------------
class MyAttendanceAPIView(ListAPIView):
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        return Attendance.objects.filter(
            user=self.request.user
        ).order_by("-date")


# -------------------------
# ATTENDANCE (ADMIN / SUPERADMIN)
# -------------------------


class UserAttendanceAPIView(ListAPIView):
    permission_classes = [IsAdmin,IsSuperAdmin]
    serializer_class = AttendanceSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        request_user = self.request.user

        # 🔐 STEP 42: Admin restriction
        if request_user.role == "ADMIN":
            allowed = EmployeeProfile.objects.filter(
                user_id=user_id,
                admin=request_user
            ).exists()

            if not allowed:
                raise PermissionDenied("This employee is not assigned to you")

        return Attendance.objects.filter(
            user_id=user_id
        ).order_by("-date")



class MyMonthlyAttendanceAPIView(ListAPIView):
    serializer_class = AttendanceReportSerializer

    def get_queryset(self):
        user = self.request.user
        month = self.request.query_params.get("month")  # YYYY-MM
        year, month = map(int, month.split("-"))

        return Attendance.objects.filter(
            user=user,
            date__year=year,
            date__month=month,
        ).order_by("date")



class EmployeeMonthlyAttendanceAPIView(ListAPIView):
    permission_classes = [IsAdmin, IsSuperAdmin]
    serializer_class = AttendanceReportSerializer

    def get_queryset(self):
        user_id = self.kwargs["user_id"]
        request_user = self.request.user

        # Admin restriction
        if request_user.role == "ADMIN":
            if not EmployeeProfile.objects.filter(
                user_id=user_id,
                admin=request_user
            ).exists():
                raise PermissionDenied("Not your employee")

        month = self.request.query_params.get("month")
        year, month = map(int, month.split("-"))

        return Attendance.objects.filter(
            user_id=user_id,
            date__year=year,
            date__month=month,
        ).order_by("date")
    
class AdminAttendanceSummaryAPIView(APIView):
    permission_classes = [IsAdmin,IsSuperAdmin]

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

class DivisionLiveLocationAPIView(APIView):
    permission_classes = [IsAdmin,IsSuperAdmin]

    def get(self, request, division_id):
        user = request.user

        employees = User.objects.filter(
            profile__division_id=division_id,
            role="EMPLOYEE"
        )

        if user.role == "ADMIN":
            employees = employees.filter(profile__admin=user)

        data = []

        for emp in employees:
            loc = LocationLog.objects.filter(
                user=emp
            ).order_by("-recorded_at").first()

            if not loc:
                continue

            data.append({
                "user_id": emp.id,
                "name": emp.full_name,
                "lat": loc.latitude,
                "lng": loc.longitude,
                "time": loc.recorded_at
            })

        return Response(data)
