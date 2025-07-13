from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
USER_AGENT = "weather-app/1.0"

# Weather code mapping for Open-Meteo API
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# Regional configuration for weather alerts and forecasts
REGION_CONFIG = {
    "uk": {
        "timezone": "Europe/London",
        "wind_thresholds": {"advisory": 30, "warning": 50, "severe": 60},
        "temp_thresholds": {"heat_advisory": 30, "cold_warning": 0, "severe_cold": -5},
        "precip_thresholds": {"advisory": 15, "warning": 25},
        "forecast_wind_thresholds": {"warning": 40, "severe": 60},
        "forecast_temp_thresholds": {"heat_warning": 32, "severe_cold": -5},
        "forecast_precip_thresholds": {"advisory": 15, "warning": 25},
    },
    "japan": {
        "timezone": "Asia/Tokyo",
        "wind_thresholds": {"advisory": 25, "warning": 40, "severe": 60, "typhoon": 60},
        "temp_thresholds": {
            "heat_advisory": 30,
            "extreme_heat": 35,
            "cold_warning": 0,
            "severe_cold": -5,
        },
        "precip_thresholds": {"advisory": 15, "warning": 30, "heavy": 50},
        "forecast_wind_thresholds": {"warning": 35, "severe": 50, "typhoon": 80},
        "forecast_temp_thresholds": {
            "heat_warning": 33,
            "extreme_heat": 38,
            "cold_warning": -3,
            "severe_cold": -10,
        },
        "forecast_precip_thresholds": {"advisory": 15, "warning": 30, "heavy": 50},
    },
}


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def build_open_meteo_url(base_url: str, params: dict[str, Any]) -> str:
    """Build Open-Meteo API URL with parameters."""
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{base_url}?{param_str}"


def extract_daily_value(
    daily_data: dict, field: str, index: int, default: Any = "N/A"
) -> Any:
    """Safely extract value from daily data array at given index."""
    field_data = daily_data.get(field, [])
    return field_data[index] if index < len(field_data) else default


def format_current_conditions(current: dict) -> str:
    """Format current weather conditions."""
    return f"""
Current Conditions:
Temperature: {current.get("temperature_2m", "N/A")}°C
Feels like: {current.get("apparent_temperature", "N/A")}°C
Humidity: {current.get("relative_humidity_2m", "N/A")}%
Wind: {current.get("wind_speed_10m", "N/A")} km/h at {current.get("wind_direction_10m", "N/A")}°
Conditions: {WEATHER_CODES.get(current.get("weather_code", 0), "Unknown")}
Precipitation: {current.get("precipitation", "N/A")} mm
"""


def format_daily_forecast(daily: dict, num_days: int = 5) -> list[str]:
    """Format daily forecast data into readable strings."""
    forecasts = []
    if not daily:
        return forecasts

    dates = daily.get("time", [])
    for i in range(min(num_days, len(dates))):
        date = dates[i]
        weather_code = extract_daily_value(daily, "weather_code", i, 0)
        temp_max = extract_daily_value(daily, "temperature_2m_max", i)
        temp_min = extract_daily_value(daily, "temperature_2m_min", i)
        precip = extract_daily_value(daily, "precipitation_sum", i)
        precip_prob = extract_daily_value(daily, "precipitation_probability_max", i)
        wind_max = extract_daily_value(daily, "wind_speed_10m_max", i)

        forecast = f"""
{date}:
High: {temp_max}°C, Low: {temp_min}°C
Conditions: {WEATHER_CODES.get(weather_code, "Unknown")}
Precipitation: {precip} mm ({precip_prob}% chance)
Max wind: {wind_max} km/h
"""
        forecasts.append(forecast)

    return forecasts


async def get_regional_forecast(latitude: float, longitude: float, region: str) -> str:
    """Get weather forecast for a region using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        region: Region name ("uk" or "japan")
    """
    if region not in REGION_CONFIG:
        return f"Unsupported region: {region}"

    config = REGION_CONFIG[region]

    # Use Open-Meteo API for weather data
    url = f"{OPEN_METEO_BASE}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_direction_10m_dominant",
        "timezone": config["timezone"],
        "forecast_days": 5,
    }

    full_url = build_open_meteo_url(url, params)
    data = await make_open_meteo_request(full_url)

    if not data:
        return f"Unable to fetch {region.upper()} weather forecast."

    # Format current conditions
    current = data.get("current", {})
    current_weather = format_current_conditions(current)

    # Format daily forecast
    daily = data.get("daily", {})
    daily_forecasts = format_daily_forecast(daily)

    forecasts = [current_weather] + daily_forecasts
    return "\n---\n".join(forecasts)


def generate_current_alerts(current: dict, config: dict, region: str) -> list[str]:
    """Generate alerts for current weather conditions."""
    alerts = []
    current_wind = current.get("wind_speed_10m", 0)
    current_temp = current.get("temperature_2m", 20)

    wind_thresholds = config["wind_thresholds"]
    temp_thresholds = config["temp_thresholds"]

    # Wind alerts
    if region == "japan" and current_wind > wind_thresholds.get("typhoon", 60):
        alerts.append(
            f"⚠️ TYPHOON/SEVERE WIND WARNING: Current wind speed is {current_wind:.1f} km/h. Extremely dangerous conditions."
        )
    elif current_wind > wind_thresholds.get("severe", 50):
        alerts.append(
            f"⚠️ HIGH WIND WARNING: Current wind speed is {current_wind:.1f} km/h. Strong winds may cause disruption."
        )
    elif current_wind > wind_thresholds.get("warning", 40):
        alerts.append(
            f"⚠️ WIND WARNING: Current wind speed is {current_wind:.1f} km/h. Strong winds may cause disruption."
        )
    elif current_wind > wind_thresholds.get("advisory", 30):
        alerts.append(
            f"⚠️ WIND ADVISORY: Current wind speed is {current_wind:.1f} km/h. Be aware of gusty conditions."
        )

    # Temperature alerts
    if region == "japan" and current_temp > temp_thresholds.get("extreme_heat", 35):
        alerts.append(
            f"🌡️ EXTREME HEAT WARNING: Current temperature is {current_temp:.1f}°C. Risk of heat stroke. Stay indoors with air conditioning."
        )
    elif current_temp > temp_thresholds.get("heat_advisory", 30):
        heat_msg = (
            "Risk of heat stroke. Stay indoors with air conditioning."
            if region == "japan" and current_temp > 35
            else "Stay hydrated and avoid prolonged sun exposure."
        )
        alerts.append(
            f"🌡️ HEAT ADVISORY: Current temperature is {current_temp:.1f}°C. {heat_msg}"
        )
    elif current_temp < temp_thresholds.get("severe_cold", -5):
        cold_msg = (
            "Risk of frostbite and dangerous driving conditions."
            if region == "japan"
            else "Risk of severe frost."
        )
        alerts.append(
            f"🥶 SEVERE COLD WARNING: Current temperature is {current_temp:.1f}°C. {cold_msg}"
        )
    elif current_temp < temp_thresholds.get("cold_warning", 0):
        alerts.append(
            f"🥶 COLD WEATHER WARNING: Current temperature is {current_temp:.1f}°C. Risk of ice and freezing conditions."
        )

    return alerts


def generate_forecast_alerts(
    daily: dict, config: dict, region: str, num_days: int = 3
) -> list[str]:
    """Generate alerts for forecast conditions."""
    alerts = []
    if not daily:
        return alerts

    dates = daily.get("time", [])
    wind_thresholds = config["forecast_wind_thresholds"]
    temp_thresholds = config["forecast_temp_thresholds"]
    precip_thresholds = config["forecast_precip_thresholds"]

    for i in range(min(num_days, len(dates))):
        date = dates[i]
        wind_max = extract_daily_value(daily, "wind_speed_10m_max", i, 0)
        temp_max = extract_daily_value(daily, "temperature_2m_max", i, 20)
        temp_min = extract_daily_value(daily, "temperature_2m_min", i, 10)
        precip = extract_daily_value(daily, "precipitation_sum", i, 0)

        # Wind warnings
        if region == "japan" and wind_max > wind_thresholds.get("typhoon", 80):
            alerts.append(
                f"🌪️ TYPHOON WARNING for {date}: Expected wind speeds up to {wind_max:.1f} km/h. Extremely dangerous conditions."
            )
        elif wind_max > wind_thresholds.get("severe", 60):
            alert_type = (
                "🌪️ SEVERE WIND WARNING"
                if region == "japan"
                else "🌪️ SEVERE WIND WARNING"
            )
            alerts.append(
                f"{alert_type} for {date}: Expected wind speeds up to {wind_max:.1f} km/h. Significant disruption possible."
            )
        elif wind_max > wind_thresholds.get("warning", 40):
            alerts.append(
                f"💨 WIND WARNING for {date}: Expected wind speeds up to {wind_max:.1f} km/h."
            )

        # Temperature warnings
        if region == "japan" and temp_max > temp_thresholds.get("extreme_heat", 38):
            alerts.append(
                f"🔥 EXTREME HEAT WARNING for {date}: Expected maximum temperature {temp_max:.1f}°C. Dangerous heat conditions."
            )
        elif temp_max > temp_thresholds.get("heat_warning", 32):
            alerts.append(
                f"🔥 HEAT WARNING for {date}: Expected maximum temperature {temp_max:.1f}°C. Very hot conditions."
            )
        elif temp_min < temp_thresholds.get("severe_cold", -5):
            cold_msg = (
                "Risk of severe frost and dangerous conditions."
                if region == "japan"
                else "Risk of severe frost."
            )
            alerts.append(
                f"❄️ SEVERE COLD WARNING for {date}: Expected minimum temperature {temp_min:.1f}°C. {cold_msg}"
            )
        elif temp_min < temp_thresholds.get("cold_warning", 0):
            alerts.append(
                f"❄️ COLD WARNING for {date}: Expected minimum temperature {temp_min:.1f}°C. Risk of frost and icy conditions."
            )

        # Precipitation warnings
        if region == "japan" and precip > precip_thresholds.get("heavy", 50):
            alerts.append(
                f"🌧️ HEAVY RAIN WARNING for {date}: Expected precipitation {precip:.1f} mm. Risk of flooding and landslides."
            )
        elif precip > precip_thresholds.get("warning", 25):
            rain_msg = "Possible flooding." if region == "uk" else "Possible flooding."
            if region == "japan":
                rain_msg = "Possible flooding."
            alerts.append(
                f"🌧️ RAIN WARNING for {date}: Expected precipitation {precip:.1f} mm. {rain_msg}"
            )
        elif precip > precip_thresholds.get("advisory", 15):
            alerts.append(
                f"🌦️ RAIN ADVISORY for {date}: Expected precipitation {precip:.1f} mm."
            )

    return alerts


async def get_regional_weather_alerts(
    latitude: float, longitude: float, region: str
) -> str:
    """Get weather alerts for a region using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
        region: Region name ("uk" or "japan")
    """
    if region not in REGION_CONFIG:
        return f"Unsupported region: {region}"

    config = REGION_CONFIG[region]

    # Use Open-Meteo API to get weather alerts
    url = f"{OPEN_METEO_BASE}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": config["timezone"],
        "forecast_days": 3,
    }

    full_url = build_open_meteo_url(url, params)
    data = await make_open_meteo_request(full_url)

    if not data:
        return f"Unable to fetch {region.upper()} weather alerts."

    current = data.get("current", {})
    daily = data.get("daily", {})

    # Generate alerts
    current_alerts = generate_current_alerts(current, config, region)
    forecast_alerts = generate_forecast_alerts(daily, config, region)

    all_alerts = current_alerts + forecast_alerts

    if not all_alerts:
        return "No significant weather alerts for this location. Current conditions are within normal ranges."

    return "\n\n".join(all_alerts)


async def make_open_meteo_request(url: str) -> dict[str, Any] | None:
    """Make a request to the Open-Meteo API with proper error handling."""
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None


def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state.

    Args:
        state: Two-letter US state code (e.g. CA, NY)
    """
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)

    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."

    if not data["features"]:
        return "No active alerts for this state."

    alerts = [format_alert(feature) for feature in data["features"]]
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # First get the forecast grid endpoint
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)

    if not points_data:
        return "Unable to fetch forecast data for this location."

    # Get the forecast URL from the points response
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)

    if not forecast_data:
        return "Unable to fetch detailed forecast."

    # Format the periods into a readable forecast
    periods = forecast_data["properties"]["periods"]
    forecasts = []
    for period in periods[:5]:  # Only show next 5 periods
        forecast = f"""
{period["name"]}:
Temperature: {period["temperature"]}°{period["temperatureUnit"]}
Wind: {period["windSpeed"]} {period["windDirection"]}
Forecast: {period["detailedForecast"]}
"""
        forecasts.append(forecast)

    return "\n---\n".join(forecasts)


@mcp.tool()
async def get_uk_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a UK location using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    return await get_regional_forecast(latitude, longitude, "uk")


@mcp.tool()
async def get_uk_weather_alerts(latitude: float, longitude: float) -> str:
    """Get weather alerts for a UK location using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    return await get_regional_weather_alerts(latitude, longitude, "uk")


@mcp.tool()
async def get_japan_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a Japan location using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    return await get_regional_forecast(latitude, longitude, "japan")


@mcp.tool()
async def get_japan_weather_alerts(latitude: float, longitude: float) -> str:
    """Get weather alerts for a Japan location using Open-Meteo API.

    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    return await get_regional_weather_alerts(latitude, longitude, "japan")


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
