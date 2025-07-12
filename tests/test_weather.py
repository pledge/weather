import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os

# Add the parent directory to the path so we can import weather
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import weather


class TestUSWeatherFunctions:
    """Test US weather functions with mocked API calls."""

    @pytest.mark.asyncio
    async def test_get_alerts_success(self):
        """Test successful weather alerts retrieval."""
        mock_response = {
            "features": [
                {
                    "properties": {
                        "event": "Severe Thunderstorm Warning",
                        "areaDesc": "Northern California",
                        "severity": "Severe",
                        "description": "Severe thunderstorms expected",
                        "instruction": "Take immediate shelter",
                    }
                }
            ]
        }

        with patch("weather.make_nws_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await weather.get_alerts("CA")

            assert "Severe Thunderstorm Warning" in result
            assert "Northern California" in result
            assert "Severe" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_alerts_no_alerts(self):
        """Test weather alerts when no alerts are active."""
        mock_response = {"features": []}

        with patch("weather.make_nws_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await weather.get_alerts("CA")

            assert "No active alerts" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_alerts_api_failure(self):
        """Test weather alerts when API call fails."""
        with patch("weather.make_nws_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await weather.get_alerts("CA")

            assert "Unable to fetch alerts" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_forecast_success(self):
        """Test successful weather forecast retrieval."""
        mock_points_response = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/MTR/85,105/forecast"
            }
        }

        mock_forecast_response = {
            "properties": {
                "periods": [
                    {
                        "name": "Today",
                        "temperature": 75,
                        "temperatureUnit": "F",
                        "windSpeed": "10 mph",
                        "windDirection": "NW",
                        "detailedForecast": "Partly cloudy with a high of 75.",
                    },
                    {
                        "name": "Tonight",
                        "temperature": 55,
                        "temperatureUnit": "F",
                        "windSpeed": "5 mph",
                        "windDirection": "W",
                        "detailedForecast": "Mostly clear with a low of 55.",
                    },
                ]
            }
        }

        with patch("weather.make_nws_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_points_response, mock_forecast_response]

            result = await weather.get_forecast(37.7749, -122.4194)

            assert "Today" in result
            assert "75°F" in result
            assert "Partly cloudy" in result
            assert "Tonight" in result
            assert mock_request.call_count == 2

    @pytest.mark.asyncio
    async def test_get_forecast_points_failure(self):
        """Test forecast when points API call fails."""
        with patch("weather.make_nws_request", new_callable=AsyncMock) as mock_request:
            mock_request.return_value = None

            result = await weather.get_forecast(37.7749, -122.4194)

            assert "Unable to fetch forecast data" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_forecast_detailed_failure(self):
        """Test forecast when detailed forecast API call fails."""
        mock_points_response = {
            "properties": {
                "forecast": "https://api.weather.gov/gridpoints/MTR/85,105/forecast"
            }
        }

        with patch("weather.make_nws_request", new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = [mock_points_response, None]

            result = await weather.get_forecast(37.7749, -122.4194)

            assert "Unable to fetch detailed forecast" in result
            assert mock_request.call_count == 2


class TestUKWeatherFunctions:
    """Test UK weather functions with mocked API calls."""

    @pytest.mark.asyncio
    async def test_get_uk_forecast_success(self):
        """Test successful UK weather forecast retrieval."""
        mock_response = {
            "current": {
                "temperature_2m": 22.5,
                "apparent_temperature": 24.1,
                "relative_humidity_2m": 65,
                "wind_speed_10m": 15.2,
                "wind_direction_10m": 225,
                "weather_code": 1,
                "precipitation": 0.0,
            },
            "daily": {
                "time": ["2025-07-11", "2025-07-12", "2025-07-13"],
                "weather_code": [1, 2, 61],
                "temperature_2m_max": [25.5, 23.1, 19.8],
                "temperature_2m_min": [15.2, 16.8, 14.5],
                "precipitation_sum": [0.0, 2.1, 8.5],
                "precipitation_probability_max": [10, 25, 75],
                "wind_speed_10m_max": [18.5, 22.1, 35.2],
            },
        }

        with patch(
            "weather.make_open_meteo_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await weather.get_uk_forecast(51.5074, -0.1278)

            assert "Current Conditions" in result
            assert "22.5°C" in result
            assert "24.1°C" in result  # feels like
            assert "65%" in result  # humidity
            assert "2025-07-11" in result
            assert "25.5°C" in result  # max temp
            assert "Mainly clear" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uk_forecast_api_failure(self):
        """Test UK forecast when API call fails."""
        with patch(
            "weather.make_open_meteo_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = None

            result = await weather.get_uk_forecast(51.5074, -0.1278)

            assert "Unable to fetch UK weather forecast" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uk_weather_alerts_no_alerts(self):
        """Test UK weather alerts when no severe conditions."""
        mock_response = {
            "current": {
                "temperature_2m": 20.0,
                "weather_code": 1,
                "wind_speed_10m": 15.0,
            },
            "daily": {
                "time": ["2025-07-11", "2025-07-12"],
                "weather_code": [1, 2],
                "temperature_2m_max": [25.0, 23.0],
                "temperature_2m_min": [15.0, 16.0],
                "precipitation_sum": [0.0, 2.0],
                "wind_speed_10m_max": [20.0, 18.0],
            },
        }

        with patch(
            "weather.make_open_meteo_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await weather.get_uk_weather_alerts(51.5074, -0.1278)

            assert "No significant weather alerts" in result
            assert "normal ranges" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uk_weather_alerts_with_warnings(self):
        """Test UK weather alerts with severe conditions."""
        mock_response = {
            "current": {
                "temperature_2m": 35.0,  # Heat warning
                "weather_code": 1,
                "wind_speed_10m": 55.0,  # High wind warning
            },
            "daily": {
                "time": ["2025-07-11", "2025-07-12"],
                "weather_code": [1, 2],
                "temperature_2m_max": [38.0, 25.0],  # Extreme heat
                "temperature_2m_min": [20.0, 16.0],
                "precipitation_sum": [0.0, 30.0],  # Heavy rain
                "wind_speed_10m_max": [65.0, 25.0],  # Severe wind
            },
        }

        with patch(
            "weather.make_open_meteo_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await weather.get_uk_weather_alerts(51.5074, -0.1278)

            assert "HIGH WIND WARNING" in result
            assert "55.0 km/h" in result
            assert "HEAT ADVISORY" in result
            assert "35.0°C" in result
            assert "HEAT WARNING" in result
            assert "38.0°C" in result
            assert "HEAVY RAIN WARNING" in result
            assert "30.0 mm" in result
            assert "SEVERE WIND WARNING" in result
            assert "65.0 km/h" in result
            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uk_weather_alerts_moderate_conditions(self):
        """Test UK weather alerts with moderate warning conditions."""
        mock_response = {
            "current": {
                "temperature_2m": -2.0,  # Cold weather warning
                "weather_code": 1,
                "wind_speed_10m": 35.0,  # Wind advisory
            },
            "daily": {
                "time": ["2025-07-11", "2025-07-12", "2025-07-13"],
                "weather_code": [1, 2, 3],
                "temperature_2m_max": [25.0, 34.0, 22.0],  # Heat warning on day 2
                "temperature_2m_min": [15.0, 20.0, -8.0],  # Severe cold on day 3
                "precipitation_sum": [0.0, 18.0, 5.0],  # Rain advisory on day 2
                "wind_speed_10m_max": [20.0, 45.0, 25.0],  # Wind warning on day 2
            },
        }

        with patch(
            "weather.make_open_meteo_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = mock_response

            result = await weather.get_uk_weather_alerts(51.5074, -0.1278)

            # Test moderate wind advisory (line 275)
            assert "WIND ADVISORY" in result
            assert "35.0 km/h" in result

            # Test cold weather warning (line 289)
            assert "COLD WEATHER WARNING" in result
            assert "-2.0°C" in result

            # Test wind warning in forecast (line 329)
            assert "WIND WARNING for 2025-07-12" in result
            assert "45.0 km/h" in result

            # Test heat warning in forecast (line 343)
            assert "HEAT WARNING for 2025-07-12" in result
            assert "34.0°C" in result

            # Test severe cold warning
            assert "SEVERE COLD WARNING for 2025-07-13" in result
            assert "-8.0°C" in result

            # Test rain advisory (line 357)
            assert "RAIN ADVISORY for 2025-07-12" in result
            assert "18.0 mm" in result

            mock_request.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_uk_weather_alerts_api_failure(self):
        """Test UK weather alerts when API call fails."""
        with patch(
            "weather.make_open_meteo_request", new_callable=AsyncMock
        ) as mock_request:
            mock_request.return_value = None

            result = await weather.get_uk_weather_alerts(51.5074, -0.1278)

            assert "Unable to fetch UK weather alerts" in result
            mock_request.assert_called_once()


class TestHelperFunctions:
    """Test helper functions."""

    @pytest.mark.asyncio
    async def test_make_nws_request_success(self):
        """Test successful NWS API request."""
        mock_response_data = {"test": "data"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await weather.make_nws_request("https://test.com")

            assert result == mock_response_data

    @pytest.mark.asyncio
    async def test_make_nws_request_failure(self):
        """Test NWS API request failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await weather.make_nws_request("https://test.com")

            assert result is None

    @pytest.mark.asyncio
    async def test_make_open_meteo_request_success(self):
        """Test successful Open-Meteo API request."""
        mock_response_data = {"test": "data"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await weather.make_open_meteo_request("https://test.com")

            assert result == mock_response_data

    @pytest.mark.asyncio
    async def test_make_open_meteo_request_failure(self):
        """Test Open-Meteo API request failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("Network error")
            )

            result = await weather.make_open_meteo_request("https://test.com")

            assert result is None

    def test_format_alert(self):
        """Test alert formatting function."""
        mock_feature = {
            "properties": {
                "event": "Test Event",
                "areaDesc": "Test Area",
                "severity": "Severe",
                "description": "Test description",
                "instruction": "Test instruction",
            }
        }

        result = weather.format_alert(mock_feature)

        assert "Test Event" in result
        assert "Test Area" in result
        assert "Severe" in result
        assert "Test description" in result
        assert "Test instruction" in result

    def test_format_alert_missing_fields(self):
        """Test alert formatting with missing fields."""
        mock_feature = {"properties": {}}

        result = weather.format_alert(mock_feature)

        assert "Unknown" in result
        assert "No description available" in result
        assert "No specific instructions provided" in result
