# =====================================================================
# File: accounts/apps.py
# Purpose: App configuration for accounts.
# Contains:
#   - AccountsConfig: registers the app and loads signals on startup.
# =====================================================================

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from . import signals  # noqa: F401  (registers the signal)