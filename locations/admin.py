from django.contrib import admin
from .models import LocationLog,Attendance,Office ,GeofenceEvent
# Register your models here.

admin.site.register(LocationLog)
admin.site.register(Office)
admin.site.register(Attendance)
admin.site.register(GeofenceEvent)