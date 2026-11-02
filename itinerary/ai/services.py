from decimal import Decimal
from django.db import transaction

from itinerary.models import AIPlan, ItineraryItem
from itinerary.ai.gemini_client import generate_itinerary
from itinerary.ai.prompts import build_itinerary_prompt
from itinerary.ai.validators import validate_itinerary


@transaction.atomic
def generate_and_save_itinerary(trip):

    # Step 1: Build prompt using trip information
    prompt = build_itinerary_prompt(trip)

    # Step 2: Generate itinerary using Gemini
    ai_data = generate_itinerary(prompt)

    # Step 3: Validate Gemini response
    validate_itinerary(ai_data)

    # Step 4: Create AI Plan
    ai_plan = AIPlan.objects.create(
        trip=trip,
        status=AIPlan.Status.GENERATED
    )

    # Step 5: Prepare itinerary activities
    items = []

    for day in ai_data["days"]:

        day_number = day["day_number"]

        for index, activity in enumerate(day["activities"]):

            items.append(
                ItineraryItem(
                    ai_plan=ai_plan,
                    day_number=day_number,
                    time_block=activity["time_block"],
                    title=activity["title"],
                    description=activity["description"],
                    activity_type=activity["activity_type"],
                    location=activity["location"],
                    estimated_cost=Decimal(
                        str(activity["estimated_cost"])
                    ),
                    order=index
                )
            )

    # Step 6: Save all activities in database
    ItineraryItem.objects.bulk_create(items)

    return ai_plan
