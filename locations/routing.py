from django.urls import path
from .consumers import LocationConsumer, DivisionLocationConsumer

websocket_urlpatterns = [
    # এমপ্লয়ি এই লিঙ্কে কানেক্ট হয়ে লোকেশন পাঠাবে
    path('ws/location/', LocationConsumer.as_asgi()),
    # অ্যাডমিন এই লিঙ্কে কানেক্ট হয়ে পুরো ডিভিশনের মুভমেন্ট দেখবে
    path("ws/locations/division/<int:division_id>/", DivisionLocationConsumer.as_asgi()),
]