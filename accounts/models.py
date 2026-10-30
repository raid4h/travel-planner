# =====================================================================
# File: accounts/models.py
# Purpose: Database models for the accounts app.
# Contains:
#   - Profile: extra info about a user (home country, bio).
# =====================================================================

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extra information about a user. One Profile per User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    home_country = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"