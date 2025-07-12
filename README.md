# Weather MCP Server

A Model Context Protocol (MCP) server that provides weather data from the National Weather Service API.

## Features

- **US Weather Alerts**: Get active weather alerts for any US state
- **US Weather Forecasts**: Get detailed weather forecasts for US locations using latitude/longitude coordinates
- **UK Weather Forecasts**: Get detailed weather forecasts for UK locations using latitude/longitude coordinates
- **UK Weather Alerts**: Get weather alerts and warnings for UK locations
- **NWS Integration**: Uses the official National Weather Service API for reliable US weather data
- **Open-Meteo Integration**: Uses Open-Meteo API for UK weather data with high-resolution forecasts

## Tools

### US Weather Tools

#### `get_alerts(state: str)`
Get weather alerts for a US state.

**Parameters:**
- `state`: Two-letter US state code (e.g., "CA", "NY")

**Returns:** Active weather alerts including event type, area description, severity, and instructions.

#### `get_forecast(latitude: float, longitude: float)`
Get weather forecast for a US location.

**Parameters:**
- `latitude`: Latitude of the location
- `longitude`: Longitude of the location

**Returns:** Weather forecast for the next 5 periods including temperature, wind, and detailed forecast.

### UK Weather Tools

#### `get_uk_forecast(latitude: float, longitude: float)`
Get weather forecast for a UK location using Open-Meteo API.

**Parameters:**
- `latitude`: Latitude of the location
- `longitude`: Longitude of the location

**Returns:** Current conditions and 5-day forecast with temperature, precipitation, wind, and weather conditions in metric units.

#### `get_uk_weather_alerts(latitude: float, longitude: float)`
Get weather alerts and warnings for a UK location.

**Parameters:**
- `latitude`: Latitude of the location
- `longitude`: Longitude of the location

**Returns:** Weather alerts for severe conditions including wind, temperature, and precipitation warnings.

## Installation

1. Install dependencies:
```bash
uv install
```

2. Install test dependencies (optional):
```bash
uv add --group test pytest pytest-asyncio pytest-mock
```

3. Run the server:
```bash
uv run weather.py
```

## Testing

Run the unit tests:
```bash
uv run pytest
```

Run tests with coverage:
```bash
uv run pytest --cov=weather
```

The test suite includes:
- Unit tests for all weather functions
- Mocked API calls (no real API requests)
- Tests for error handling and edge cases
- Fast execution (all tests complete in seconds)

## Usage

This server is designed to be used with MCP-compatible clients. The server runs on stdio transport and provides weather data through the MCP protocol.

## Requirements

- Python 3.13+
- httpx
- mcp[cli]

## APIs

- **National Weather Service API** (https://api.weather.gov): Provides free weather data for the United States
- **Open-Meteo API** (https://open-meteo.com): Provides free weather data for the UK using high-resolution Met Office models

## Example Usage

### US Weather
```python
# Get weather alerts for California
get_alerts("CA")

# Get US weather forecast for New York City
get_forecast(40.7128, -74.0060)
```

### UK Weather
```python
# Get UK weather forecast for London
get_uk_forecast(51.5074, -0.1278)

# Get UK weather alerts for Manchester
get_uk_weather_alerts(53.4808, -2.2426)
```