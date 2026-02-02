from rest_framework import serializers
from .models import User, EmployeeProfile,Division, FCMToken


# users/serializers.py

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'role')

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data.get('full_name', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'EMPLOYEE')
        )
        return user

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    # এমপ্লয়ি তৈরির জন্য এটি ইনপুট হিসেবে নিবে
    division_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('email', 'name', 'password', 'role', 'division_id')

    def validate(self, attrs):
        role = attrs.get('role', 'EMPLOYEE')
        division_id = attrs.get('division_id')

        # ১. ইউজার তৈরির আগেই চেক করে নিন এমপ্লয়ির ডিভিশন আইডি আছে কি না
        if role == 'EMPLOYEE' and not division_id:
            raise serializers.ValidationError({"division_id": "Employee must be assigned to a division."})
        
        if division_id and not Division.objects.filter(id=division_id).exists():
            raise serializers.ValidationError({"division_id": "Invalid division ID."})
            
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        division_id = validated_data.pop('division_id', None)
        
        # ২. create_user ব্যবহার করলে পাসওয়ার্ড অটোমেটিক হ্যাশ হয় এবং লগইন কাজ করে
        user = User.objects.create_user(
            email=validated_data['email'],
            name=validated_data.get('name', ''),
            password=password,
            role=validated_data.get('role', 'EMPLOYEE'),
            is_active=True
        )

        # ৩. এমপ্লয়ি প্রোফাইল এবং ডিভিশন সেট করা
        if user.role == 'EMPLOYEE':
            EmployeeProfile.objects.update_or_create(
                user=user,
                defaults={'division_id': division_id}
            )
            
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
