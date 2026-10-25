# =====================================================================
# File: accounts/forms.py
# Purpose: Forms for signing up, logging in, editing the profile and
#          changing the password.
# Contains:
#   - StyledFormMixin: gives fields the Tailwind "form-input" look and
#     a red outline when a field has an error
#   - RegisterForm: Full Name, Email, Password, Confirm Password.
#     The email is also stored as the Django username, so people log
#     in with their email address.
#   - EmailLoginForm: Email, Password and a "Remember me" checkbox
#   - ProfileForm: edit Full Name, Home Country and Bio (email is
#     shown on the page but cannot be changed here)
#   - StyledPasswordChangeForm: Current / New / Confirm New Password
# =====================================================================

from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError

User = get_user_model()

INPUT_CLASS = "form-input"
INVALID_CLASS = "form-input is-invalid"
PASSWORD_DOTS = "•" * 8  # the "........" shown inside empty password boxes


class StyledFormMixin:
    """Adds the Tailwind classes from static/src/input.css to every field."""

    # If True, a form-level error (e.g. "wrong password") outlines all fields.
    highlight_all_on_form_error = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = INPUT_CLASS

    def full_clean(self):
        super().full_clean()
        if not self.is_bound:
            return
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                continue
            has_error = name in self._errors or (
                self.highlight_all_on_form_error and "__all__" in self._errors
            )
            if has_error:
                field.widget.attrs["class"] = INVALID_CLASS


def split_full_name(full_name):
    """'Alex Morgan Lee' -> ('Alex', 'Morgan Lee'). Django stores first/last."""
    parts = full_name.split()
    first = parts[0][:150] if parts else ""
    last = " ".join(parts[1:])[:150]
    return first, last


class RegisterForm(StyledFormMixin, forms.Form):
    full_name = forms.CharField(
        label="Full Name",
        max_length=150,
        widget=forms.TextInput(
            attrs={"placeholder": "Alex Morgan", "autocomplete": "name", "autofocus": True}
        ),
    )
    email = forms.EmailField(
        label="Email Address",
        max_length=150,
        widget=forms.EmailInput(
            attrs={"placeholder": "alex@example.com", "autocomplete": "email"}
        ),
    )
    password1 = forms.CharField(
        label="Password",
        strip=False,
        help_text="Use at least 8 characters.",
        widget=forms.PasswordInput(
            attrs={"placeholder": PASSWORD_DOTS, "autocomplete": "new-password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": PASSWORD_DOTS, "autocomplete": "new-password"}
        ),
    )

    def clean_full_name(self):
        # Collapse extra spaces: "  Alex   Morgan " -> "Alex Morgan"
        return " ".join(self.cleaned_data["full_name"].split())

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        taken = (
            User.objects.filter(username__iexact=email).exists()
            or User.objects.filter(email__iexact=email).exists()
        )
        if taken:
            raise ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "The two passwords do not match.")
        elif password1:
            # Check strength; the temporary user lets Django reject
            # passwords that are too similar to the name or email.
            first, last = split_full_name(cleaned.get("full_name", ""))
            candidate = User(
                username=cleaned.get("email", ""),
                email=cleaned.get("email", ""),
                first_name=first,
                last_name=last,
            )
            try:
                password_validation.validate_password(password1, candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        return cleaned

    def save(self):
        """Create and return the new user (the Profile is made by a signal)."""
        first, last = split_full_name(self.cleaned_data["full_name"])
        email = self.cleaned_data["email"]
        return User.objects.create_user(
            username=email,
            email=email,
            password=self.cleaned_data["password1"],
            first_name=first,
            last_name=last,
        )


class EmailLoginForm(StyledFormMixin, AuthenticationForm):
    """Django's login form, but the user types an email, not a username."""

    highlight_all_on_form_error = True

    # Django calls the login field "username"; here it holds the email.
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(
            attrs={"placeholder": "alex@example.com", "autocomplete": "email", "autofocus": True}
        ),
    )
    password = forms.CharField(
        label="Password",
        strip=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": PASSWORD_DOTS, "autocomplete": "current-password"}
        ),
    )
    remember_me = forms.BooleanField(
        label="Remember me on this device", required=False, initial=True
    )

    error_messages = {
        "invalid_login": "Incorrect email or password.",
        "inactive": "This account is inactive.",
    }

    def clean_username(self):
        # Emails are saved in lower case, so compare in lower case.
        return self.cleaned_data["username"].strip().lower()


class ProfileForm(StyledFormMixin, forms.Form):
    """Edit the logged-in user's name and profile details."""

    full_name = forms.CharField(
        label="Full Name",
        max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    home_country = forms.CharField(
        label="Home Country",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "e.g. Bangladesh"}),
    )
    bio = forms.CharField(
        label="Bio",
        max_length=500,
        required=False,
        help_text="A few words about you and how you like to travel (max 500 characters).",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "Tell us about your travel style"}),
    )

    def __init__(self, *args, user, **kwargs):
        self.user = user
        # Pre-fill the form with what is already saved.
        saved = {
            "full_name": user.get_full_name(),
            "home_country": user.profile.home_country,
            "bio": user.profile.bio,
        }
        # FormView passes initial={} (empty), so merge instead of setdefault.
        kwargs["initial"] = {**saved, **(kwargs.get("initial") or {})}
        super().__init__(*args, **kwargs)

    def clean_full_name(self):
        return " ".join(self.cleaned_data["full_name"].split())

    def save(self):
        first, last = split_full_name(self.cleaned_data["full_name"])
        self.user.first_name = first
        self.user.last_name = last
        self.user.save(update_fields=["first_name", "last_name"])

        profile = self.user.profile
        profile.home_country = self.cleaned_data["home_country"].strip()
        profile.bio = self.cleaned_data["bio"].strip()
        profile.save()
        return self.user


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    """Django's change-password form with our labels and styling."""

    highlight_all_on_form_error = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "Current Password"
        self.fields["new_password1"].label = "New Password"
        self.fields["new_password1"].help_text = "Use at least 8 characters."
        self.fields["new_password2"].label = "Confirm New Password"
        self.fields["old_password"].widget.attrs.pop("autofocus", None)