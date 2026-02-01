from rest_framework import serializers
from .models import User, EmployeeProfile,Division, FCMToken

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'role']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()       

        if user.role == 'EMPLOYEE':
            EmployeeProfile.objects.create(user=user)
        if user.role == "EMPLOYEE" and not validated_data.get("division"):
            raise serializers.ValidationError("division_id is required")
        return user
    
class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ["id", "name"]

class EmployeeMiniSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    division = serializers.CharField(source="profile.division.name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "division"]

    # Adding '-> str' fixes the warning
    def get_full_name(self, obj) -> str:
        # Use `name` field on the custom User model, fallback to email
        name_val = getattr(obj, "name", None)
        if name_val:
            return name_val
        return obj.email
    
class FCMTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMToken
        fields = ["token", "device_type"]
