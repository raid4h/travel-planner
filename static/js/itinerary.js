document.addEventListener("DOMContentLoaded", function () {
    const tripSelect = document.getElementById("tripSelect");
    const generateBtn = document.getElementById("generateBtn");
    const statusMessage = document.getElementById("statusMessage");
    const itineraryResult = document.getElementById("itineraryResult");

    if (!tripSelect || !generateBtn) {
        return;
    }

    generateBtn.addEventListener("click", async function () {
        const tripId = tripSelect.value;

        if (!tripId) {
            statusMessage.textContent = "Please select a trip first.";
            return;
        }

        generateBtn.disabled = true;
        generateBtn.textContent = "Generating...";
        statusMessage.textContent = "AI is preparing your itinerary...";
        itineraryResult.innerHTML = "";

        try {
            const response = await fetch("/api/itineraries/generate/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": getCookie("csrftoken")
                },
                body: JSON.stringify({
                    trip_id: tripId
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.error || "Failed to generate itinerary."
                );
            }

            statusMessage.textContent = data.message;
            displayItinerary(data.plan);

        } catch (error) {
            console.error("Itinerary Error:", error);
            statusMessage.textContent = error.message;

        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = "Generate AI Itinerary";
        }
    });

    function displayItinerary(plan) {
        itineraryResult.innerHTML = "";

        const heading = document.createElement("h2");
        heading.className = "mb-6 text-2xl font-bold text-gray-900";
        heading.textContent = "Your AI Generated Itinerary";

        itineraryResult.appendChild(heading);

        const groupedDays = {};

        plan.items.forEach(function (item) {
            if (!groupedDays[item.day_number]) {
                groupedDays[item.day_number] = [];
            }

            groupedDays[item.day_number].push(item);
        });

        Object.keys(groupedDays)
            .sort(function (a, b) {
                return Number(a) - Number(b);
            })
            .forEach(function (dayNumber) {
                const daySection = document.createElement("section");

                daySection.className =
                    "mb-6 rounded-xl border bg-white p-6 shadow-sm";

                const dayTitle = document.createElement("h3");

                dayTitle.className =
                    "mb-4 text-xl font-bold text-blue-700";

                dayTitle.textContent = "Day " + dayNumber;

                daySection.appendChild(dayTitle);

                groupedDays[dayNumber].forEach(function (activity) {
                    const card = document.createElement("div");

                    card.className =
                        "mb-4 rounded-lg border border-gray-200 p-4";

                    const title = document.createElement("h4");
                    title.className = "font-semibold text-gray-900";
                    title.textContent = activity.title;

                    const time = document.createElement("p");
                    time.className = "mt-1 text-sm text-blue-600";
                    time.textContent = activity.time_block;

                    const description = document.createElement("p");
                    description.className = "mt-2 text-gray-600";
                    description.textContent = activity.description;

                    const location = document.createElement("p");
                    location.className = "mt-2 text-sm text-gray-700";
                    location.textContent =
                        "Location: " + activity.location;

                    const cost = document.createElement("p");
                    cost.className =
                        "mt-1 text-sm font-medium text-gray-800";

                    cost.textContent =
                        "Estimated Cost: " + activity.estimated_cost;

                    card.appendChild(title);
                    card.appendChild(time);
                    card.appendChild(description);
                    card.appendChild(location);
                    card.appendChild(cost);

                    daySection.appendChild(card);
                });

                itineraryResult.appendChild(daySection);
            });
    }

    function getCookie(name) {
        const cookies = document.cookie.split(";");

        for (let cookie of cookies) {
            cookie = cookie.trim();

            if (cookie.startsWith(name + "=")) {
                return decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
            }
        }

        return "";
    }
});