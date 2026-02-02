import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware:
    """
    Custom middleware to authenticate users using a JWT token in the query string.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # কুয়েরি প্যারামিটার থেকে টোকেন বের করা: ws://.../?token=XYZ
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]

        if token:
            try:
                # টোকেন ডিকোড করা
                decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = decoded_data.get("user_id")
                scope["user"] = await get_user(user_id)
            except (jwt.ExpiredSignatureError, jwt.DecodeError, KeyError):
                scope["user"] = AnonymousUser()
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)