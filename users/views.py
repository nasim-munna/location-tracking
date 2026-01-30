from rest_framework.viewsets import ModelViewSet
from .models import User,Division,FCMToken
from .serializers import UserCreateSerializer,DivisionSerializer,EmployeeMiniSerializer,FCMTokenSerializer
from .permissions import IsSuperAdmin,IsAdmin
from rest_framework.generics import ListAPIView
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [IsSuperAdmin]

def PermissionDenied(*args, **kwargs):
    raise NotImplementedError


def perform_update(self, serializer):
    if 'role' in serializer.validated_data:
        raise PermissionDenied("Role cannot be changed")
    serializer.save()


class DivisionListAPIView(ListAPIView):
    serializer_class = DivisionSerializer
    permission_classes = [IsAdmin,IsSuperAdmin]
    queryset = Division.objects.all()

class DivisionEmployeeAPIView(ListAPIView):
    serializer_class = EmployeeMiniSerializer
    permission_classes = [IsAdmin,IsSuperAdmin]

    def get_queryset(self):
        division_id = self.kwargs["division_id"]
        user = self.request.user

        qs = User.objects.filter(
            profile__division_id=division_id,
            role="EMPLOYEE"
        )

        if user.role == "ADMIN":
            qs = qs.filter(profile__admin=user)

        return qs

# Add this import at the top


class SaveFCMTokenAPIView(APIView):
    permission_classes = [IsAuthenticated]

    # This tells Swagger to use FCMTokenSerializer for the request body
    @extend_schema(
        request=FCMTokenSerializer,
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}}
    )
    def post(self, request):
        serializer = FCMTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        FCMToken.objects.update_or_create(
            token=serializer.validated_data["token"],
            defaults={
                "user": request.user,
                "device_type": serializer.validated_data["device_type"]
            }
        )

        return Response({"status": "token_saved"})