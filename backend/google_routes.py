import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_ROUTES_API_KEY = os.getenv("GOOGLE_ROUTES_API_KEY")

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"


def get_google_route(
    origin_lat,
    origin_lng,
    destination_lat,
    destination_lng
):
    if not GOOGLE_ROUTES_API_KEY:
        raise RuntimeError(
            "GOOGLE_ROUTES_API_KEY is missing in backend/.env"
        )

    payload = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": origin_lat,
                    "longitude": origin_lng
                }
            }
        },

        "destination": {
            "location": {
                "latLng": {
                    "latitude": destination_lat,
                    "longitude": destination_lng
                }
            }
        },

        "travelMode": "DRIVE",

        "routingPreference": "TRAFFIC_AWARE",

        "computeAlternativeRoutes": False,

        "languageCode": "en-US",

        "units": "METRIC"
    }

    headers = {
        "Content-Type": "application/json",

        "X-Goog-Api-Key":
            GOOGLE_ROUTES_API_KEY,

        "X-Goog-FieldMask":
            "routes.duration,"
            "routes.distanceMeters,"
            "routes.polyline.encodedPolyline"
    }

    response = requests.post(
        ROUTES_URL,
        json=payload,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("routes"):
        raise RuntimeError(
            "Google Maps did not return a route."
        )

    route = data["routes"][0]

    distance_meters = route.get(
        "distanceMeters",
        0
    )

    return {
        "distance_meters": distance_meters,

        "distance_km": round(
            distance_meters / 1000,
            2
        ),

        "duration": route.get(
            "duration",
            "0s"
        ),

        "polyline": route[
            "polyline"
        ][
            "encodedPolyline"
        ]
    }