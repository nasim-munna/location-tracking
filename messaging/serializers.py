from rest_framework import serializers
from .models import Message

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(
        source="sender.full_name",
        read_only=True
    )
    receiver_name = serializers.CharField(
        source="receiver.full_name",
        read_only=True
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "sender_name",
            "receiver",
            "receiver_name",
            "text",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["sender", "is_read", "created_at"]

class BroadcastMessageSerializer(serializers.Serializer):
    division_id = serializers.IntegerField()
    text = serializers.CharField()
