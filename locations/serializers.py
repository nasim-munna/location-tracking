from rest_framework import serializers
from .models import LocationLog, Attendance,GeofenceEvent
from datetime import datetime
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field # Import this if using drf-spectacular

# -------------------------
# CREATE (INPUT) SERIALIZER
# -------------------------
class LocationCreateSerializer(serializers.ModelSerializer):
    # 'millis' ke IntegerField hishebe define kora jate Django error na dey
    millis = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = LocationLog
        fields = ['latitude', 'longitude', 'millis']

    def create(self, validated_data):
        # millis data-ti niye recorded_at field-e convert kora (optional logic)
        millis = validated_data.pop('millis', None)
        if millis:
            # millisecond ke datetime object-e convert kora
            validated_data['recorded_at'] = datetime.fromtimestamp(millis / 1000.0)
        
        return super().create(validated_data)


# -------------------------
# READ (OUTPUT) SERIALIZER
# -------------------------
class LocationReadSerializer(serializers.ModelSerializer):
    millis = serializers.SerializerMethodField()

    class Meta:
        model = LocationLog
        fields = ['id', 'latitude', 'longitude', 'millis', 'recorded_at', 'created_at']

    # Add '-> int' to fix the type hint warning
    def get_millis(self, obj) -> int:
        if obj.recorded_at:
            return int(obj.recorded_at.timestamp() * 1000)
        return 0
# -------------------------
# ATTENDANCE SERIALIZER
# -------------------------
class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'




class AttendanceReportSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    late_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'date',
            'check_in',
            'check_out',
            'status',
            'late_minutes',
        ]

    # Add -> str to tell the documentation it returns a string
    def get_status(self, obj) -> str:
        if not obj.check_in:
            return "ABSENT"

        office = obj.office
        if obj.check_in.time() > office.work_start_time:
            return "LATE"

        return "PRESENT"

    # Add -> int to tell the documentation it returns an integer
    def get_late_minutes(self, obj) -> int:
        if not obj.check_in:
            return 0

        office = obj.office
        start_dt = timezone.make_aware(
            datetime.combine(obj.date, office.work_start_time)
        )

        if obj.check_in <= start_dt:
            return 0

        return int((obj.check_in - start_dt).total_seconds() / 60)


class GeofenceEventSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source="user.full_name",
        read_only=True
    )

    class Meta:
        model = GeofenceEvent
        fields = [
            "id",
            "user",
            "user_name",
            "event",
            "occurred_at",
        ]
