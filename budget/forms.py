from decimal import Decimal

from django import forms

from .models import Expense

INPUT_CLASSES = (
    "w-full rounded-lg border border-gray-300 bg-white px-3.5 py-2 text-sm "
    "text-gray-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20"
)


class SetBudgetForm(forms.Form):
    budget = forms.DecimalField(
        min_value=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(
            attrs={
                "step": "0.01",
                "min": "0",
                "placeholder": "e.g. 3000.00",
                "class": INPUT_CLASSES,
            }
        ),
    )


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "category", "amount", "date", "notes"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "placeholder": "e.g. Roundtrip Flights or Hotel Shinjuku",
                    "class": INPUT_CLASSES,
                }
            ),
            "category": forms.Select(attrs={"class": INPUT_CLASSES}),
            "amount": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0.01",
                    "placeholder": "0.00",
                    "class": INPUT_CLASSES,
                }
            ),
            "date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": INPUT_CLASSES,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Optional notes (e.g. 5 nights, bullet train pass...)",
                    "class": INPUT_CLASSES,
                }
            ),
        }

