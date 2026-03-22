"""
Agent tools for search, weather, directions, timezone, and currency exchange.

Each tool is a Strands @tool decorated function that the agent can invoke.
Tools are kept in this separate module so they can be:
- Reused across different agents
- Tested independently
- Expanded into multiple files as the tool list grows

All tool log messages are prefixed with [Tool] for easy filtering in debug.log:
    grep "\\[Tool\\]" debug.log
"""

import json
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from ddgs import DDGS
from strands.tools.decorator import tool


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s,p%(process)s,{%(filename)s:%(lineno)d},%(levelname)s,%(message)s",
)
logger = logging.getLogger(__name__)


# Constants
NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org/search"
OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"
OPEN_METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
FRANKFURTER_API_BASE_URL = "https://api.frankfurter.app/latest"
NOMINATIM_USER_AGENT = "simple-agent-evals/1.0"
HTTP_TIMEOUT_SECONDS = 10

# Simple city-to-timezone mapping for common cities
CITY_TIMEZONE_MAP = {
    "tokyo": "Asia/Tokyo",
    "london": "Europe/London",
    "paris": "Europe/Paris",
    "new york": "America/New_York",
    "los angeles": "America/Los_Angeles",
    "chicago": "America/Chicago",
    "denver": "America/Denver",
    "sydney": "Australia/Sydney",
    "berlin": "Europe/Berlin",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "singapore": "Asia/Singapore",
    "dubai": "Asia/Dubai",
    "moscow": "Europe/Moscow",
    "sao paulo": "America/Sao_Paulo",
    "toronto": "America/Toronto",
    "seoul": "Asia/Seoul",
    "hong kong": "Asia/Hong_Kong",
    "bangkok": "Asia/Bangkok",
    "istanbul": "Europe/Istanbul",
    "rome": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "amsterdam": "Europe/Amsterdam",
    "seattle": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "boston": "America/New_York",
    "washington dc": "America/New_York",
    "miami": "America/New_York",
    "austin": "America/Chicago",
    "nashville": "America/Chicago",
    "anchorage": "America/Anchorage",
    "honolulu": "Pacific/Honolulu",
}


# ---------------------------------------------------------------------------
# Private helpers (used by the public tool functions below)
# ---------------------------------------------------------------------------


def _geocode_location(
    place_name: str
) -> dict:
    """
    Convert a place name to latitude/longitude using Nominatim.

    Args:
        place_name: Name of the place to geocode

    Returns:
        Dictionary with lat, lon, and display_name
    """
    logger.info(f"[Tool] Geocoding location: {place_name}")

    response = requests.get(
        NOMINATIM_BASE_URL,
        params={
            "q": place_name,
            "format": "json",
            "limit": 1,
        },
        headers={"User-Agent": NOMINATIM_USER_AGENT},
        timeout=HTTP_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    results = response.json()

    if not results:
        raise ValueError(f"Could not find location: {place_name}")

    result = results[0]
    logger.info(f"[Tool] Geocoded '{place_name}' to: {result['display_name']}")

    return {
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
        "display_name": result["display_name"],
    }


def _format_duration(
    duration_seconds: float
) -> str:
    """
    Format duration in seconds to a human-readable string.

    Args:
        duration_seconds: Duration in seconds

    Returns:
        Formatted string like '1 hour 23 minutes'
    """
    hours = int(duration_seconds // 3600)
    minutes = int((duration_seconds % 3600) // 60)

    parts = []
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if not parts:
        parts.append("less than 1 minute")

    return " ".join(parts)


def _format_distance(
    distance_meters: float
) -> str:
    """
    Format distance in meters to miles.

    Args:
        distance_meters: Distance in meters

    Returns:
        Formatted string like '15.3 miles'
    """
    miles = distance_meters / 1609.34
    return f"{miles:.1f} miles"


def _resolve_timezone(
    city: str
) -> str:
    """
    Resolve a city name to a timezone identifier using the local mapping.

    Args:
        city: City name (e.g. "Tokyo", "New York")

    Returns:
        Timezone identifier string (e.g. "Asia/Tokyo")
    """
    city_lower = city.lower().strip()

    if city_lower in CITY_TIMEZONE_MAP:
        tz = CITY_TIMEZONE_MAP[city_lower]
        logger.info(f"[Tool] Resolved '{city}' to timezone '{tz}'")
        return tz

    raise ValueError(
        f"Could not find timezone for city: {city}. "
        f"Supported cities: {', '.join(sorted(CITY_TIMEZONE_MAP.keys()))}"
    )


# ---------------------------------------------------------------------------
# Public tool functions (registered with the Strands agent)
# ---------------------------------------------------------------------------


@tool
def duckduckgo_search(
    query: str,
    max_results: int = 5
) -> str:
    """
    Search DuckDuckGo for the given query. Use this for current events,
    news, general information, or any topic that requires web search.

    Args:
        query: The search query string
        max_results: Maximum number of results to return

    Returns:
        JSON string containing search results
    """
    try:
        logger.info(f"[Tool] duckduckgo_search: query='{query}', max_results={max_results}")

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))

        logger.info(f"[Tool] duckduckgo_search: found {len(results)} results")
        return json.dumps(results, indent=2)

    except Exception as e:
        logger.error(f"[Tool] duckduckgo_search failed: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_weather(
    location: str
) -> str:
    """
    Get current weather for a location using Open-Meteo API (free, no API key needed).
    Use this when users ask about weather, temperature, or conditions in a place.

    Args:
        location: Name of the city or place (e.g. 'Washington DC', 'Tokyo', 'London')

    Returns:
        JSON string with current weather data including temperature, conditions, wind, humidity
    """
    try:
        logger.info(f"[Tool] get_weather: location='{location}'")

        geo = _geocode_location(location)

        response = requests.get(
            OPEN_METEO_BASE_URL,
            params={
                "latitude": geo["lat"],
                "longitude": geo["lon"],
                "current_weather": "true",
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
                "temperature_unit": "fahrenheit",
                "wind_speed_unit": "mph",
            },
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        current = data.get("current", data.get("current_weather", {}))

        weather_info = {
            "location": geo["display_name"],
            "temperature_f": current.get("temperature_2m", current.get("temperature")),
            "wind_speed_mph": current.get("wind_speed_10m", current.get("windspeed")),
            "humidity_percent": current.get("relative_humidity_2m"),
            "weather_code": current.get("weather_code", current.get("weathercode")),
        }

        logger.info(f"[Tool] get_weather: {location} -> {weather_info['temperature_f']}F")
        return json.dumps(weather_info, indent=2)

    except Exception as e:
        logger.error(f"[Tool] get_weather failed: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_directions(
    origin: str,
    destination: str
) -> str:
    """
    Get driving directions between two locations using OSRM (free, no API key needed).
    Use this when users ask about travel time, distance, or directions between places.

    Args:
        origin: Starting location name (e.g. 'Washington DC', 'WAS17 Amazon office Arlington VA')
        destination: Destination location name (e.g. 'Georgetown University', 'New York City')

    Returns:
        JSON string with route info including distance, duration, and turn-by-turn steps
    """
    try:
        logger.info(f"[Tool] get_directions: '{origin}' -> '{destination}'")

        origin_geo = _geocode_location(origin)
        # Small delay to respect Nominatim rate limits
        time.sleep(1)
        dest_geo = _geocode_location(destination)

        coords = f"{origin_geo['lon']},{origin_geo['lat']};{dest_geo['lon']},{dest_geo['lat']}"
        url = f"{OSRM_BASE_URL}/{coords}"

        response = requests.get(
            url,
            params={
                "overview": "false",
                "steps": "true",
                "geometries": "geojson",
            },
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            logger.warning("[Tool] get_directions: no route found")
            return json.dumps({"error": "No route found between these locations"})

        route = data["routes"][0]

        steps = []
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                if step.get("name") and step.get("maneuver", {}).get("type") != "depart":
                    steps.append({
                        "instruction": f"{step['maneuver'].get('type', '')} onto {step['name']}",
                        "distance": _format_distance(step["distance"]),
                        "duration": _format_duration(step["duration"]),
                    })

        directions_info = {
            "origin": origin_geo["display_name"],
            "destination": dest_geo["display_name"],
            "total_distance": _format_distance(route["distance"]),
            "total_duration": _format_duration(route["duration"]),
            "steps": steps[:10],
        }

        logger.info(
            f"[Tool] get_directions: {directions_info['total_distance']}, "
            f"{directions_info['total_duration']}"
        )
        return json.dumps(directions_info, indent=2)

    except Exception as e:
        logger.error(f"[Tool] get_directions failed: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_current_time(
    city: str
) -> str:
    """
    Get the current local time for a city using Python's zoneinfo (no external API needed).
    Use this when users ask about the current time in a specific city or timezone.

    Args:
        city: Name of the city (e.g. 'Tokyo', 'New York', 'London')

    Returns:
        JSON string with current local time, timezone name, and UTC offset
    """
    try:
        logger.info(f"[Tool] get_current_time: city='{city}'")

        timezone_id = _resolve_timezone(city)
        tz = ZoneInfo(timezone_id)
        now = datetime.now(tz)

        utc_offset = now.strftime("%z")
        # Format as +HH:MM
        utc_offset_formatted = f"{utc_offset[:3]}:{utc_offset[3:]}"

        time_info = {
            "city": city,
            "timezone": timezone_id,
            "datetime": now.isoformat(),
            "utc_offset": utc_offset_formatted,
            "abbreviation": now.strftime("%Z"),
        }

        logger.info(
            f"[Tool] get_current_time: {city} -> "
            f"{time_info['datetime']} ({time_info['abbreviation']})"
        )
        return json.dumps(time_info, indent=2)

    except Exception as e:
        logger.error(f"[Tool] get_current_time failed: {e}")
        return json.dumps({"error": str(e)})


@tool
def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    amount: float = 1.0
) -> str:
    """
    Get the current exchange rate between two currencies using the Frankfurter API
    (free, no API key needed). Use this when users ask about currency conversion
    or exchange rates.

    Args:
        from_currency: Source currency code (e.g. 'USD', 'EUR', 'GBP')
        to_currency: Target currency code (e.g. 'JPY', 'EUR', 'GBP')
        amount: Amount to convert (default 1.0)

    Returns:
        JSON string with exchange rate and converted amount
    """
    try:
        from_code = from_currency.upper().strip()
        to_code = to_currency.upper().strip()

        logger.info(
            f"[Tool] get_exchange_rate: {amount} {from_code} -> {to_code}"
        )

        response = requests.get(
            FRANKFURTER_API_BASE_URL,
            params={
                "from": from_code,
                "to": to_code,
                "amount": amount,
            },
            timeout=HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()

        rates = data.get("rates", {})
        converted_amount = rates.get(to_code)

        exchange_info = {
            "from_currency": from_code,
            "to_currency": to_code,
            "amount": amount,
            "rate": converted_amount / amount if converted_amount and amount else None,
            "converted_amount": converted_amount,
            "date": data.get("date", ""),
        }

        logger.info(
            f"[Tool] get_exchange_rate: {amount} {from_code} = "
            f"{converted_amount} {to_code}"
        )
        return json.dumps(exchange_info, indent=2)

    except Exception as e:
        logger.error(f"[Tool] get_exchange_rate failed: {e}")
        return json.dumps({"error": str(e)})
