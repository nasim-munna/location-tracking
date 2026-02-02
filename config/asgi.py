import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from locations.middleware import JWTAuthMiddleware  # আপনার পাথ অনুযায়ী ইম্পোর্ট করুন
import locations.routing
import messaging.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(  # এখানে কাস্টম মিডলওয়্যার ব্যবহার করা হয়েছে
        URLRouter(
            locations.routing.websocket_urlpatterns +
            messaging.routing.websocket_urlpatterns
        )
    ),
})