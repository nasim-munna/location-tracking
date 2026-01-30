# locations/throttles.py
from rest_framework.throttling import UserRateThrottle

class GPSThrottle(UserRateThrottle):
    scope = "gps"
