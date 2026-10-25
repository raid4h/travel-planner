# =====================================================================
# File: accounts/views.py
# Purpose: The "controllers" for the public/account pages. A view
#          receives a request from the browser and returns a page.
# Contains:
#   - landing_page: the public home page (logged-in users are sent on
#     to their trips)
#   - RegisterView: sign-up page; logs the new user in afterwards
#   - EmailLoginView: login page; supports "Remember me"
#   - LogoutView: logs the user out (POST only) and shows a message
#   - ProfileView: "My Profile" page to edit name, country and bio
#   - PasswordChangeView: change password while staying logged in
# =====================================================================

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView

from .forms import (
    EmailLoginForm,
    ProfileForm,
    RegisterForm,
    StyledPasswordChangeForm,
)

# How long "Remember me" keeps someone logged in (14 days, in seconds).
REMEMBER_ME_SECONDS = 60 * 60 * 24 * 14


def landing_page(request):
    """Public home page. People who are already logged in skip it."""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    return render(request, "accounts/landing.html")


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = RegisterForm

    def dispatch(self, request, *args, **kwargs):
        # No need to register again when already logged in.
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)  # log the new user in straight away
        messages.success(self.request, f"Welcome to Travel Planner, {user.first_name}!")
        return redirect(settings.LOGIN_REDIRECT_URL)


class EmailLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True  # already logged in -> skip this page

    def form_valid(self, form):
        response = super().form_valid(form)  # logs the user in
        if form.cleaned_data.get("remember_me"):
            self.request.session.set_expiry(REMEMBER_ME_SECONDS)
        else:
            self.request.session.set_expiry(0)  # ends when the browser closes
        messages.success(self.request, "Welcome back!")
        return response


class LogoutView(auth_views.LogoutView):
    """Logout only accepts POST (the navbar button is a small form)."""

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have been logged out.")
        return response


class ProfileView(LoginRequiredMixin, FormView):
    """Show and edit the logged-in user's profile."""

    template_name = "accounts/profile.html"
    form_class = ProfileForm
    success_url = reverse_lazy("accounts:profile")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user  # ProfileForm needs to know who
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your profile has been updated.")
        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    """Change password. Django keeps the user logged in afterwards."""

    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form)