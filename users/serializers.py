from rest_framework import serializers
from .models import User, EmployeeProfile,Division

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

        return user
    
class DivisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Division
        fields = ["id", "name"]

class EmployeeMiniSerializer(serializers.ModelSerializer):
    # 'full_name' field toiri korar jonno MethodField use kora hoyeche
    full_name = serializers.SerializerMethodField()
    division = serializers.CharField(source="profile.division.name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "full_name", "email", "division"]

    # Ei function-ti first_name ebong last_name ke eksathe kore full_name banabe
    def get_full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else obj.username
