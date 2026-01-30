import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from users.models import User, EmployeeProfile


class LocationConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.request_user = self.scope["user"]

        # Must be authenticated
        if not self.request_user.is_authenticated:
            await self.close()
            return

        self.employee_id = self.scope["url_route"]["kwargs"]["user_id"]

        # Permission check
        allowed = await self.is_allowed()
        if not allowed:
            await self.close()
            return

        self.group_name = f"location_{self.employee_id}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def send_location(self, event):
        await self.send(text_data=json.dumps(event["data"]))

    # -------------------------
    # PERMISSION LOGIC
    # -------------------------
    @database_sync_to_async
    def is_allowed(self):
        try:
            employee = User.objects.get(id=self.employee_id)
        except User.DoesNotExist:
            return False

        # SuperAdmin can see anyone
        if self.request_user.role == "SUPERADMIN":
            return True

        # Admin can see only assigned employees
        if self.request_user.role == "ADMIN":
            return EmployeeProfile.objects.filter(
                user=employee,
                admin=self.request_user
            ).exists()

        # Employee cannot watch anyone
        return False
