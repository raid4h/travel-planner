# =====================================================================
# File: accounts/signals.py
# Purpose: Automatic actions that run when user records change.
# Contains:
#   - create_profile_for_new_user: creates an empty Profile whenever
#     a new User is created.
# =====================================================================

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_for_new_user(sender, instance, created, **kwargs):
    """Every time a new User is created, create an empty Profile for them."""
    if created:
        Profile.objects.create(user=instance)