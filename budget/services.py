import json
import os
import re
import threading
from decimal import Decimal, InvalidOperation

import requests
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce

from .models import Expense

DEFAULT_GEMINI_MODEL = "gemini-3-flash-preview"
GEMINI_API_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

CATEGORY_COLORS = {
    Expense.Category.FOOD: "#f59e0b",
    Expense.Category.TRANSPORT: "#3b82f6",
    Expense.Category.ACCOMMODATION: "#8b5cf6",
    Expense.Category.ACTIVITIES: "#10b981",
    Expense.Category.SHOPPING: "#ec4899",
    Expense.Category.OTHER: "#6b7280",
}


class AIBudgetError(Exception):
    """Raised when Gemini AI budget/pricing generation fails."""


class GeminiKeyRotator:
    """Thread-safe round-robin API key rotator with failover ordering."""

    def __init__(self):
        self._lock = threading.Lock()
        self._index = 0
        self._cached_raw = None
        self._keys = []

    def _load_keys(self):
        raw_multi = os.getenv("GEMINI_API_KEYS", "")
        raw_single = os.getenv("GEMINI_API_KEY", "")
        combined = f"{raw_multi},{raw_single}"
        if combined != self._cached_raw:
            seen = []
            for part in combined.split(","):
                cleaned = part.strip()
                if cleaned and cleaned not in seen:
                    seen.append(cleaned)
            self._keys = seen
            self._cached_raw = combined
            if self._keys:
                self._index = self._index % len(self._keys)
            else:
                self._index = 0

    def get_ordered_keys_for_request(self):
        """
        Returns all configured keys rotated so the next round-robin key is first,
        followed by fallback keys if the primary key hits a rate/permission error.
        """
        with self._lock:
            self._load_keys()
            if not self._keys:
                return []
            start = self._index % len(self._keys)
            self._index = (start + 1) % len(self._keys)
            return [
                self._keys[(start + offset) % len(self._keys)]
                for offset in range(len(self._keys))
            ]


key_rotator = GeminiKeyRotator()


def _to_decimal(value, default="0.00"):
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(default)


def get_trip_budget_summary(trip):
    """Calculates total spending, remaining budget, and category breakdown via ORM."""
    totals = trip.expenses.aggregate(
        total_spent=Coalesce(Sum("amount"), Decimal("0.00")),
        expense_count=Count("id"),
    )
    total_budget = _to_decimal(trip.budget)
    total_spent = _to_decimal(totals["total_spent"])
    remaining_budget = total_budget - total_spent
    is_over_budget = remaining_budget < Decimal("0.00")

    if total_budget > Decimal("0.00"):
        raw_pct = float((total_spent / total_budget) * Decimal("100"))
        percent_used = round(raw_pct, 1)
        progress_bar_width = min(max(raw_pct, 0.0), 100.0)
    else:
        percent_used = 100.0 if total_spent > Decimal("0.00") else 0.0
        progress_bar_width = 100.0 if total_spent > Decimal("0.00") else 0.0

    grouped_rows = {
        row["category"]: row
        for row in trip.expenses.values("category").annotate(
            total=Coalesce(Sum("amount"), Decimal("0.00")),
            count=Count("id"),
        )
    }

    category_breakdown = []
    for code, label in Expense.Category.choices:
        row = grouped_rows.get(code)
        cat_amount = _to_decimal(row["total"]) if row else Decimal("0.00")
        cat_count = row["count"] if row else 0
        share_pct = (
            round(float((cat_amount / total_spent) * Decimal("100")), 1)
            if total_spent > Decimal("0.00")
            else 0.0
        )
        category_breakdown.append(
            {
                "category": code,
                "label": label,
                "amount": cat_amount,
                "count": cat_count,
                "percentage": share_pct,
                "color": CATEGORY_COLORS.get(code, "#6b7280"),
            }
        )

    return {
        "trip_id": trip.id,
        "currency": trip.currency,
        "total_budget": total_budget,
        "total_spent": total_spent,
        "remaining_budget": remaining_budget,
        "remaining_abs": abs(remaining_budget),
        "expense_count": totals["expense_count"],
        "is_over_budget": is_over_budget,
        "percent_used": percent_used,
        "progress_bar_width": round(progress_bar_width, 1),
        "category_breakdown": category_breakdown,
    }


def set_trip_budget(trip, amount):
    """Updates overall Trip.budget safely."""
    cleaned = _to_decimal(amount, default="-1")
    if cleaned < Decimal("0.00"):
        raise ValueError("Budget cannot be negative.")
    trip.budget = cleaned
    trip.save(update_fields=["budget", "updated_at"])
    return trip


def _build_budget_prompt(trip):
    interests_str = ", ".join(trip.interests) if trip.interests else "general sightseeing"
    existing_budget_hint = (
        f"The traveler currently has a target budget of {trip.budget} {trip.currency}."
        if trip.budget and trip.budget > 0
        else "The traveler has not set a target budget yet; propose a realistic overall budget."
    )
    notes_hint = f"Additional traveler notes: {trip.notes}" if trip.notes else ""

    return f"""You are a travel cost estimation specialist. Propose realistic trip pricing and an itemized expense plan.

Trip details:
- Title: {trip.title}
- Destination: {trip.destination}, {trip.country}
- Dates: {trip.start_date} to {trip.end_date} ({trip.duration_days} days)
- Travelers: {trip.travelers} person(s)
- Travel Style: {trip.get_travel_style_display()} ({trip.travel_style})
- Interests: {interests_str}
- Currency: {trip.currency}
- {existing_budget_hint}
{notes_hint}

Return ONLY valid JSON with this exact schema:
{{
  "recommended_total_budget": 2500.00,
  "summary": "Brief 1-2 sentence overview of the pricing rationale.",
  "categories": [
    {{"category": "accommodation", "estimated_amount": 900.00, "rationale": "Short note"}},
    {{"category": "food", "estimated_amount": 500.00, "rationale": "Short note"}},
    {{"category": "transport", "estimated_amount": 600.00, "rationale": "Short note"}},
    {{"category": "activities", "estimated_amount": 300.00, "rationale": "Short note"}},
    {{"category": "shopping", "estimated_amount": 120.00, "rationale": "Short note"}},
    {{"category": "other", "estimated_amount": 80.00, "rationale": "Short note"}}
  ],
  "proposed_expenses": [
    {{
      "title": "Specific realistic expense item name",
      "category": "accommodation|food|transport|activities|shopping|other",
      "amount": 900.00,
      "notes": "Brief explanation of unit cost / nights / travelers"
    }}
  ]
}}

Rules:
1. All monetary numbers must be in {trip.currency} and greater than 0 where applicable.
2. Provide 6 to 10 realistic proposed_expenses covering the trip's key costs.
3. The sum of proposed_expenses amounts should equal recommended_total_budget.
4. Category values MUST strictly be one of: food, transport, accommodation, activities, shopping, other.
"""


def _extract_gemini_text(payload):
    candidates = payload.get("candidates") or []
    if not candidates:
        raise AIBudgetError("Gemini returned no candidates.")
    parts = candidates[0].get("content", {}).get("parts") or []
    non_thought_texts = [
        p["text"] for p in parts if "text" in p and not p.get("thought", False)
    ]
    raw_text = "\n".join(non_thought_texts).strip()
    if not raw_text and parts:
        raw_text = "\n".join(p.get("text", "") for p in parts).strip()
    if not raw_text:
        raise AIBudgetError("Gemini returned an empty response.")
    # Strip markdown fences if present
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)
    return raw_text


def _normalize_ai_proposal(data, currency):
    if not isinstance(data, dict):
        raise AIBudgetError("AI response was not a JSON object.")

    valid_categories = dict(Expense.Category.choices)
    normalized_expenses = []
    for item in data.get("proposed_expenses") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()[:150]
        cat = str(item.get("category") or "other").strip().lower()
        if cat not in valid_categories:
            cat = Expense.Category.OTHER
        amount = _to_decimal(item.get("amount"), default="0.00")
        if not title or amount <= Decimal("0.00"):
            continue
        normalized_expenses.append(
            {
                "title": title,
                "category": cat,
                "category_label": valid_categories[cat],
                "amount": str(amount),
                "notes": str(item.get("notes") or "").strip()[:500],
            }
        )

    if not normalized_expenses:
        raise AIBudgetError("AI did not return valid proposed expense items.")

    normalized_categories = []
    seen_cats = set()
    for cat_item in data.get("categories") or []:
        if not isinstance(cat_item, dict):
            continue
        cat = str(cat_item.get("category") or "").strip().lower()
        if cat not in valid_categories or cat in seen_cats:
            continue
        seen_cats.add(cat)
        est = _to_decimal(cat_item.get("estimated_amount"), default="0.00")
        normalized_categories.append(
            {
                "category": cat,
                "label": valid_categories[cat],
                "estimated_amount": str(max(est, Decimal("0.00"))),
                "rationale": str(cat_item.get("rationale") or "").strip()[:300],
            }
        )

    expenses_sum = sum((_to_decimal(x["amount"]) for x in normalized_expenses), Decimal("0.00"))
    rec_total = _to_decimal(data.get("recommended_total_budget"), default="0.00")
    if rec_total <= Decimal("0.00"):
        rec_total = expenses_sum

    return {
        "currency": currency,
        "recommended_total_budget": str(rec_total),
        "proposed_items_total": str(expenses_sum),
        "summary": str(data.get("summary") or "AI-estimated budget based on your trip details.").strip(),
        "categories": normalized_categories,
        "proposed_expenses": normalized_expenses,
    }


def propose_trip_budget_with_ai(trip):
    """
    Calls Google Gemini API using round-robin key rotation + automatic failover
    to propose overall trip budget and itemized category pricing.
    """
    ordered_keys = key_rotator.get_ordered_keys_for_request()
    if not ordered_keys:
        raise AIBudgetError(
            "No Gemini API key configured. Add GEMINI_API_KEYS to your .env file."
        )

    model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
    url = GEMINI_API_URL_TEMPLATE.format(model=model)
    prompt = _build_budget_prompt(trip)

    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.4,
        },
    }

    last_error = None
    for api_key in ordered_keys:
        try:
            resp = requests.post(
                url,
                params={"key": api_key},
                json=request_body,
                timeout=30,
            )
        except requests.RequestException as exc:
            last_error = f"Network error contacting Gemini API: {exc}"
            continue

        if resp.status_code == 200:
            try:
                raw_json_text = _extract_gemini_text(resp.json())
                parsed = json.loads(raw_json_text)
                return _normalize_ai_proposal(parsed, trip.currency)
            except (ValueError, KeyError, AIBudgetError) as exc:
                last_error = f"Failed to parse AI pricing response: {exc}"
                continue

        # Retryable across key pool: rate limit (429), permission/quota (403), transient server error (500/503)
        if resp.status_code in (403, 429, 500, 502, 503, 504):
            try:
                detail = resp.json().get("error", {}).get("message", resp.text[:150])
            except ValueError:
                detail = resp.text[:150]
            last_error = f"Gemini HTTP {resp.status_code}: {detail}"
            continue

        # Non-retryable client error (e.g., 400/404 bad model)
        try:
            detail = resp.json().get("error", {}).get("message", resp.text[:150])
        except ValueError:
            detail = resp.text[:150]
        raise AIBudgetError(f"Gemini API error ({resp.status_code}): {detail}")

    raise AIBudgetError(
        last_error or "All configured Gemini API keys failed or hit rate limits."
    )


@transaction.atomic
def apply_ai_proposal(
    trip,
    recommended_budget=None,
    proposed_expenses=None,
    replace_existing_ai=True,
):
    """Saves AI-proposed overall budget and/or itemized expenses to PostgreSQL."""
    if recommended_budget is not None:
        budget_dec = _to_decimal(recommended_budget, default="-1")
        if budget_dec >= Decimal("0.00"):
            trip.budget = budget_dec
            trip.save(update_fields=["budget", "updated_at"])

    created_expenses = []
    if proposed_expenses:
        if replace_existing_ai:
            trip.expenses.filter(is_ai_generated=True).delete()

        valid_categories = {code for code, _ in Expense.Category.choices}
        for item in proposed_expenses:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()[:150]
            cat = str(item.get("category") or "other").strip().lower()
            if cat not in valid_categories:
                cat = Expense.Category.OTHER
            amount = _to_decimal(item.get("amount"), default="0.00")
            if not title or amount <= Decimal("0.00"):
                continue
            created_expenses.append(
                Expense.objects.create(
                    trip=trip,
                    title=title,
                    category=cat,
                    amount=amount,
                    date=trip.start_date,
                    notes=str(item.get("notes") or "").strip()[:500],
                    is_ai_generated=True,
                )
            )

    return created_expenses

