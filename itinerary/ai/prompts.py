import json


def build_itinerary_prompt(trip):
    interests = trip.interests or []

    trip_data = {
        "destination": trip.destination,
        "country": trip.country,
        "start_date": str(trip.start_date),
        "end_date": str(trip.end_date),
        "duration_days": trip.duration_days,
        "travelers": trip.travelers,
        "travel_style": trip.travel_style,
        "interests": interests,
        "budget": str(trip.budget),
        "currency": trip.currency,
        "notes": trip.notes,
    }

    return f"""
You are an expert AI travel planner.

Create a personalized day-by-day travel itinerary
using the following trip information:

{json.dumps(trip_data, indent=2)}

IMPORTANT REQUIREMENTS:

1. Generate activities for every travel day.
2. Each day must have a day_number starting from 1.
3. Include morning, afternoon and evening activities.
4. Include sightseeing, meals, transport and rest where appropriate.
5. Every activity must include all required fields.
6. estimated_cost must be a non-negative number.
7. activity_type must be one of:
   food, sightseeing, activity, transport, rest, other.
8. Consider the traveler's budget and travel style.
9. Do not invent extra days beyond the trip duration.
10. Return valid JSON only. Do not use Markdown.

FOLLOW THIS EXACT JSON STRUCTURE:

{{
    "days": [
        {{
            "day_number": 1,
            "activities": [
                {{
                    "time_block": "Morning",
                    "title": "Visit a popular beach",
                    "description": "Enjoy the beach and nearby attractions.",
                    "activity_type": "sightseeing",
                    "location": "Cox's Bazar Beach",
                    "estimated_cost": 200
                }}
            ]
        }}
    ],
    "travel_tips": [
        "Carry drinking water.",
        "Check local weather before travelling."
    ]
}}

Do not change the JSON field names.
Do not add explanations outside the JSON.
"""
