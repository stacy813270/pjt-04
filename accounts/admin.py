from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('독서 프로필', {'fields': (
            'gender', 'age', 'weekly_reading_hours', 'annual_reading_count', 'interested_genres',
            'interested_categories',
        )}),
    )
