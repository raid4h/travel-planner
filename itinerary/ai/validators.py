def validate_itinerary(data):
    """
    Validate the JSON response received from Gemini AI.
    """

    if not isinstance(data, dict):
        raise ValueError("AI response must be a JSON object.")

    days = data.get("days")

    if not isinstance(days, list) or not days:
        raise ValueError("Itinerary must contain at least one day.")

    for day in days:
        if not isinstance(day, dict):
            raise ValueError("Invalid day format.")

        if not isinstance(day.get("day_number"), int):
            raise ValueError("Each day must have a valid day number.")

        activities = day.get("activities")

        if not isinstance(activities, list):
            raise ValueError("Activities must be a list.")

        for activity in activities:
            required_fields = [
                "time_block",
                "title",
                "description",
                "activity_type",
                "location",
                "estimated_cost",
            ]

            for field in required_fields:
                if field not in activity:
                    raise ValueError(
                        f"Activity is missing required field: {field}"
                    )

            if not isinstance(activity["estimated_cost"], (int, float)):
                raise ValueError("Activity cost must be numeric.")

            if activity["estimated_cost"] < 0:
                raise ValueError("Activity cost cannot be negative.")

    return data
