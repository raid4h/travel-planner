import os
import json
import requests

from pathlib import Path
from dotenv import load_dotenv


# Load .env from the main project folder
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


def generate_itinerary(prompt):

    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise ValueError("Gemini API key is not configured.")

    url = (
        "https://generativelanguage.googleapis.com/"
       "v1beta/models/gemini-3.8-flash:generateContent"
    )

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=(20, 120)
        )

        response.raise_for_status()

        result = response.json()

        ai_text = (
            result["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        return json.loads(ai_text)

    except requests.exceptions.HTTPError as e:
        error_message = e.response.text
        raise ValueError(
            f"Gemini API Error: {error_message}"
        ) from e

    except requests.exceptions.RequestException as e:
        raise ValueError(
            f"Gemini connection failed: {str(e)}"
        ) from e

    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        raise ValueError(
            "Gemini returned an invalid response."
        )
