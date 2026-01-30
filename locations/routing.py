from django.urls import path
from .consumers import LocationConsumer,DivisionLocationConsumer

websocket_urlpatterns = [
    path('ws/location/<uuid:user_id>/', LocationConsumer.as_asgi()),
    path("ws/locations/division/<int:division_id>/",DivisionLocationConsumer.as_asgi()),
]
