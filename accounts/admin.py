# =====================================================================
# File: accounts/admin.py
# Purpose: Shows accounts models in the Django admin site.
# Contains:
#   - ProfileAdmin: list columns and search for Profiles.
# =====================================================================

from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "home_country", "created_at")
    search_fields = ("user__username", "user__email", "home_country")