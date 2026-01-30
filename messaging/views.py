from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.exceptions import PermissionDenied
from .models import Message
from .serializers import MessageSerializer,BroadcastMessageSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import Message
from .serializers import MessageSerializer
from .permissions import CanSendMessage
from users.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404

from users.models import Division, EmployeeProfile
from rest_framework.exceptions import PermissionDenied

class SendMessageAPIView(CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated, CanSendMessage]

    def perform_create(self, serializer):
        sender = self.request.user
        receiver_id = self.request.data.get("receiver")

        try:
            receiver = User.objects.get(id=receiver_id)
        except User.DoesNotExist:
            raise PermissionDenied("Receiver not found")

        # 🔐 Role rules
        if sender.role == "EMPLOYEE" and receiver.role != "SUPERADMIN":
            raise PermissionDenied("Employees can only message SuperAdmin")

        serializer.save(sender=sender, receiver=receiver)

class InboxAPIView(ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related("sender", "receiver")

    
class UnreadCountAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        count = Message.objects.filter(
            receiver=user,
            is_read=False
        ).count()

        return Response({
            "unread_count": count
        })



class ConversationAPIView(ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        other_id = self.kwargs["user_id"]

        return Message.objects.filter(
            Q(sender=user, receiver_id=other_id) |
            Q(sender_id=other_id, receiver=user)
        ).order_by("created_at")


class MarkMessageReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        user = request.user
        message = get_object_or_404(Message, id=message_id)

        # Only receiver can mark as read
        if message.receiver != user:
            raise PermissionDenied("Not allowed")

        if not message.is_read:
            message.is_read = True
            message.save(update_fields=["is_read"])

        return Response({"status": "read"})
    
class MarkConversationReadAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        user = request.user

        Message.objects.filter(
            sender_id=user_id,
            receiver=user,
            is_read=False
        ).update(is_read=True)

        return Response({"status": "conversation_read"})




class DivisionBroadcastAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = BroadcastMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        division_id = serializer.validated_data["division_id"]
        text = serializer.validated_data["text"]

        # Only Admin / SuperAdmin
        if user.role not in ["ADMIN", "SUPERADMIN"]:
            raise PermissionDenied("Not allowed")

        try:
            division = Division.objects.get(id=division_id)
        except Division.DoesNotExist:
            raise PermissionDenied("Invalid division")

        profiles = EmployeeProfile.objects.filter(
            division=division
        )

        # Admin restriction
        if user.role == "ADMIN":
            profiles = profiles.filter(admin=user)

        messages = [
            Message(
                sender=user,
                receiver=profile.user,
                text=text
            )
            for profile in profiles
        ]

        Message.objects.bulk_create(messages)

        return Response({
            "sent_to": len(messages),
            "division": division.name
        })
