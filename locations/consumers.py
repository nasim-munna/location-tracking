import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import LocationLog

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        
        # ১. ইউজার অথেন্টিকেশন এবং রোল চেক
        if self.user.is_authenticated and self.user.role == 'EMPLOYEE':
            self.division_id = await self.get_user_division()
            
            if self.division_id:
                self.group_name = f"division_{self.division_id}"
                await self.channel_layer.group_add(self.group_name, self.channel_name)
                await self.accept()
            else:
                await self.close(code=4003) # No Division Assigned
        else:
            await self.close(code=4001) # Unauthorized

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            lat = data.get('lat')
            lng = data.get('lng')

            if lat and lng:
                # রিয়েল-টাইম ব্রডকাস্ট (সবার আগে এটি করুন যাতে অ্যাডমিন দ্রুত আপডেট পায়)
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        "type": "broadcast_location",
                        "data": {
                            "user_id": self.user.id,
                            "name": getattr(self.user, 'full_name', 'Unknown'),
                            "lat": lat,
                            "lng": lng,
                            "role": self.user.role
                        }
                    }
                )
                
                # ব্যাকগ্রাউন্ডে ডাটাবেসে সেভ
                await self.save_location_data(lat, lng)

        except Exception as e:
            # প্রোডাকশনে লগিং ব্যবহার করা ভালো
            pass 

    @database_sync_to_async
    def save_location_data(self, lat, lng):
        # এখানে চাইলে আপনি চেক করতে পারেন ইউজার গত ১ মিনিটে মুভ করেছে কি না
        return LocationLog.objects.create(
            user=self.user,
            latitude=lat,
            longitude=lng
        )

    async def broadcast_location(self, event):
        await self.send(text_data=json.dumps(event["data"]))

class DivisionLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        # শুধুমাত্র অ্যাডমিন বা সুপারঅ্যাডমিন এক্সেস পাবে
        if user.is_authenticated and user.role in ['ADMIN', 'SUPERADMIN']:
            self.division_id = self.scope["url_route"]["kwargs"]["division_id"]
            self.group_name = f"division_{self.division_id}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # এমপ্লয়ি কন্সুমার থেকে পাঠানো মেসেজ রিসিভ করা
    async def broadcast_location(self, event):
        await self.send(text_data=json.dumps(event["data"]))