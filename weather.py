from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
OPEN_METEO_BASE = "https://api.open-meteo.com/v1"
USER_AGENT = "weather-app/1.0"

async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to the NWS API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

async def make_open_meteo_request(url: str) -> dict[str, Any] | None:
    """Make a request to the Open-Meteo API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }
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
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
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
{period['name']}:
Temperature: {period['temperature']}°{period['temperatureUnit']}
Wind: {period['windSpeed']} {period['windDirection']}
Forecast: {period['detailedForecast']}
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
    # Use Open-Meteo API for UK weather data
    url = f"{OPEN_METEO_BASE}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,wind_direction_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,wind_speed_10m_max,wind_direction_10m_dominant",
        "timezone": "Europe/London",
        "forecast_days": 5
    }
    
    # Build URL with parameters
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{param_str}"
    
    data = await make_open_meteo_request(full_url)
    
    if not data:
        return "Unable to fetch UK weather forecast."
    
    # Weather code mapping
    weather_codes = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Light freezing drizzle", 57: "Dense freezing drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Light freezing rain", 67: "Heavy freezing rain",
        71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
        77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }
    
    # Format current conditions
    current = data.get("current", {})
    current_weather = f"""
Current Conditions:
Temperature: {current.get('temperature_2m', 'N/A')}°C
Feels like: {current.get('apparent_temperature', 'N/A')}°C
Humidity: {current.get('relative_humidity_2m', 'N/A')}%
Wind: {current.get('wind_speed_10m', 'N/A')} km/h at {current.get('wind_direction_10m', 'N/A')}°
Conditions: {weather_codes.get(current.get('weather_code', 0), 'Unknown')}
Precipitation: {current.get('precipitation', 'N/A')} mm
"""
    
    # Format daily forecast
    daily = data.get("daily", {})
    forecasts = [current_weather]
    
    if daily:
        dates = daily.get("time", [])
        for i in range(min(5, len(dates))):
            date = dates[i]
            weather_code = daily.get("weather_code", [])[i] if i < len(daily.get("weather_code", [])) else 0
            temp_max = daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else "N/A"
            temp_min = daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else "N/A"
            precip = daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else "N/A"
            precip_prob = daily.get("precipitation_probability_max", [])[i] if i < len(daily.get("precipitation_probability_max", [])) else "N/A"
            wind_max = daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else "N/A"
            
            forecast = f"""
{date}:
High: {temp_max}°C, Low: {temp_min}°C
Conditions: {weather_codes.get(weather_code, 'Unknown')}
Precipitation: {precip} mm ({precip_prob}% chance)
Max wind: {wind_max} km/h
"""
            forecasts.append(forecast)
    
    return "\n---\n".join(forecasts)

@mcp.tool()
async def get_uk_weather_alerts(latitude: float, longitude: float) -> str:
    """Get weather alerts for a UK location using Open-Meteo API.
    
    Args:
        latitude: Latitude of the location
        longitude: Longitude of the location
    """
    # Use Open-Meteo API to get weather alerts
    url = f"{OPEN_METEO_BASE}/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "Europe/London",
        "forecast_days": 3
    }
    
    # Build URL with parameters
    param_str = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{param_str}"
    
    data = await make_open_meteo_request(full_url)
    
    if not data:
        return "Unable to fetch UK weather alerts."
    
    alerts = []
    current = data.get("current", {})
    daily = data.get("daily", {})
    
    # Check for severe weather conditions
    current_wind = current.get("wind_speed_10m", 0)
    current_temp = current.get("temperature_2m", 20)
    
    # Wind alerts
    if current_wind > 50:
        alerts.append("⚠️ HIGH WIND WARNING: Current wind speed is {:.1f} km/h. Strong winds may cause disruption.".format(current_wind))
    elif current_wind > 30:
        alerts.append("⚠️ WIND ADVISORY: Current wind speed is {:.1f} km/h. Be aware of gusty conditions.".format(current_wind))
    
    # Temperature alerts
    if current_temp > 30:
        alerts.append("🌡️ HEAT ADVISORY: Current temperature is {:.1f}°C. Stay hydrated and avoid prolonged sun exposure.".format(current_temp))
    elif current_temp < 0:
        alerts.append("🥶 COLD WEATHER WARNING: Current temperature is {:.1f}°C. Risk of ice and freezing conditions.".format(current_temp))
    
    # Check forecast for severe conditions
    if daily:
        dates = daily.get("time", [])
        for i in range(min(3, len(dates))):
            date = dates[i]
            wind_max = daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else 0
            temp_max = daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else 20
            temp_min = daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else 10
            precip = daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0
            
            # Future wind warnings
            if wind_max > 60:
                alerts.append("🌪️ SEVERE WIND WARNING for {}: Expected wind speeds up to {:.1f} km/h. Significant disruption possible.".format(date, wind_max))
            elif wind_max > 40:
                alerts.append("💨 WIND WARNING for {}: Expected wind speeds up to {:.1f} km/h.".format(date, wind_max))
            
            # Future temperature warnings
            if temp_max > 32:
                alerts.append("🔥 HEAT WARNING for {}: Expected maximum temperature {:.1f}°C. Very hot conditions.".format(date, temp_max))
            elif temp_min < -5:
                alerts.append("❄️ SEVERE COLD WARNING for {}: Expected minimum temperature {:.1f}°C. Risk of severe frost.".format(date, temp_min))
            
            # Heavy precipitation warnings
            if precip > 25:
                alerts.append("🌧️ HEAVY RAIN WARNING for {}: Expected precipitation {:.1f} mm. Possible flooding.".format(date, precip))
            elif precip > 15:
                alerts.append("🌦️ RAIN ADVISORY for {}: Expected precipitation {:.1f} mm.".format(date, precip))
    
    if not alerts:
        return "No significant weather alerts for this location. Current conditions are within normal ranges."
    
    return "\n\n".join(alerts)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')