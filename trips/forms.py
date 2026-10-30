# =====================================================================
# File: trips/forms.py
# Purpose: The form used to create and edit a trip.
# Contains:
#   - TripForm: Title, Destination, Country, Start/End date,
#     Travelers, Travel style, Interests (free-text tags), Budget,
#     Currency and Notes.
#       * Interests arrive as one comma-separated text value
#         ("Food, Museums, Hiking") and are saved as a clean list.
#       * The owner is NOT a form field; the view sets it to the
#         logged-in user, so nobody can create trips for someone else.
#       * Date and number checks come from Trip.clean() in models.py.
# =====================================================================

from django import forms

from .models import Trip

INPUT_CLASS = "form-input"
INVALID_CLASS = "form-input is-invalid"


class TripForm(forms.ModelForm):
    # Quick-pick tags the template/JS can offer next to the Interests box.
    suggested_interests = Trip.SUGGESTED_INTERESTS
    # Replaces the model's JSON field with simple comma-separated text.
    interests = forms.CharField(
        label="Interests",
        required=False,
        help_text="Type a tag and press Enter or comma. Examples: Food, Museums, Hiking.",
        widget=forms.TextInput(attrs={"placeholder": "Food, Museums, Hiking"}),
    )

    class Meta:
        model = Trip
        fields = [
            "title",
            "destination",
            "country",
            "start_date",
            "end_date",
            "travelers",
            "travel_style",
            "interests",
            "budget",
            "currency",
            "notes",
        ]
        labels = {
            "title": "Trip Title",
            "start_date": "Start Date",
            "end_date": "End Date",
            "travel_style": "Travel Style",
            "budget": "Total Budget",
        }
        help_texts = {
            "country": "Optional.",
            "currency": "3-letter code, e.g. USD, EUR, BDT.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Summer in Tokyo", "autofocus": True}),
            "destination": forms.TextInput(attrs={"placeholder": "Tokyo"}),
            "country": forms.TextInput(attrs={"placeholder": "Japan"}),
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "end_date": forms.DateInput(attrs={"type": "date"}),
            "travelers": forms.NumberInput(attrs={"min": 1}),
            "budget": forms.NumberInput(attrs={"min": 0, "step": "0.01", "placeholder": "0.00"}),
            "currency": forms.TextInput(attrs={"maxlength": 3, "placeholder": "USD"}),
            "notes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Anything you want to remember about this trip"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # When editing, show the saved tag list as "Food, Museums".
        if self.instance and self.instance.pk:
            self.initial["interests"] = ", ".join(self.instance.interests or [])

        # Same look as the account forms.
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASS

    def full_clean(self):
        super().full_clean()
        if self.is_bound:
            for name in self.errors:
                if name in self.fields:
                    self.fields[name].widget.attrs["class"] = INVALID_CLASS

    def clean_interests(self):
        """'Food, Museums, food' -> ['Food', 'Museums'] (Trip.clean() checks limits)."""
        raw = self.cleaned_data.get("interests") or ""
        tags = []
        for part in raw.split(","):
            tag = part.strip()
            if tag and tag.lower() not in (t.lower() for t in tags):
                tags.append(tag)
        return tags

    def clean_currency(self):
        return (self.cleaned_data.get("currency") or "USD").strip().upper()