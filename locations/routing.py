from django.urls import path
from .consumers import LocationConsumer

websocket_urlpatterns = [
    path('ws/location/<uuid:user_id>/', LocationConsumer.as_asgi()),
]
