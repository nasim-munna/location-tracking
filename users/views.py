from rest_framework.viewsets import ModelViewSet
from .models import User,Division
from .serializers import UserCreateSerializer,DivisionSerializer,EmployeeMiniSerializer
from .permissions import IsSuperAdmin,IsAdmin
from rest_framework.generics import ListAPIView


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

