# users/admin.py
from django.contrib import admin
from .models import User, EmployeeProfile

admin.site.register(User)
admin.site.register(EmployeeProfile)
