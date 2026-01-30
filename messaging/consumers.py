import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async
from .models import Message

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
            return

        self.other_user_id = self.scope["url_route"]["kwargs"]["user_id"]

        users = sorted([str(self.user.id), str(self.other_user_id)])
        self.room_name = f"chat_{users[0]}_{users[1]}"

        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get("text")

        if not text:
            return

        receiver = await sync_to_async(User.objects.get)(
            id=self.other_user_id
        )

        message = await sync_to_async(Message.objects.create)(
            sender=self.user,
            receiver=receiver,
            text=text
        )

        await self.channel_layer.group_send(
            self.room_name,
            {
                "type": "chat_message",
                "message": {
                    "id": message.id,
                    "sender": str(self.user.id),
                    "receiver": str(receiver.id),
                    "text": message.text,
                    "created_at": message.created_at.isoformat(),
                }
            }
        )

    async def chat_message(self, event):
        await self.send(
            text_data=json.dumps(event["message"])
        )
