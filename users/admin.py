# users/admin.py
from django.contrib import admin
from .models import User, EmployeeProfile,Division,FCMToken

admin.site.register(User)
admin.site.register(EmployeeProfile)
admin.site.register(Division)
admin.site.register(FCMToken)