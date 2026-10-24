# =====================================================================
# File: accounts/urls.py
# Purpose: The web addresses (URLs) that belong to the accounts app.
#          config/urls.py includes this file.
# Contains:
#   /                      -> landing page          (name: accounts:landing)
#   /accounts/register/    -> sign-up page          (name: accounts:register)
#   /accounts/login/       -> login page            (name: accounts:login)
#   /accounts/logout/      -> logout (POST only)    (name: accounts:logout)
# =====================================================================

from django.urls import path

from . import views

# The namespace lets templates write {% url 'accounts:login' %}.
app_name = "accounts"

urlpatterns = [
    path("", views.landing_page, name="landing"),
    path("accounts/register/", views.RegisterView.as_view(), name="register"),
    path("accounts/login/", views.EmailLoginView.as_view(), name="login"),
    path("accounts/logout/", views.LogoutView.as_view(), name="logout"),
]