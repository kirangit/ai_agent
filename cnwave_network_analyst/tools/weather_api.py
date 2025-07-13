import requests
from urllib.parse import urlencode
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://archive-api.open-meteo.com/v1/archive"


def get_weather(latitude, longitude, start_date, end_date):
    """
    Get historical hourly precipitation data from Open-Meteo API.

    Parameters:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
        start_date (str): Start date in YYYY-MM-DD format.
        end_date (str): End date in YYYY-MM-DD format.

    Returns:
        dict: JSON response containing precipitation data or error message.
    """
    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": "precipitation"
        }

        url = f"{BASE_URL}?{urlencode(params)}"
        logger.info(f"Requesting weather data from: {url}")

        response = requests.get(url)
        response.raise_for_status()

        logger.debug("Weather API response received successfully.")
        return response.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch weather data: {e}")
        return {"status": "error", "message": str(e)}


from datetime import datetime, timezone

def get_current_utc_time() -> str:
    """
    Returns the current UTC time in ISO 8601 format (e.g., 2025-07-06T13:45:00Z).
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

