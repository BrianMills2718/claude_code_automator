from typing import Dict, Optional


class WeatherClient:
    """Client for fetching weather data (currently uses hardcoded data)."""
    
    def __init__(self) -> None:
        # Hardcoded weather data for various cities
        self._weather_data: Dict[str, Dict[str, str]] = {
            "London": {"temperature": "15°C", "description": "Partly cloudy"},
            "New York": {"temperature": "22°C", "description": "Sunny"},
            "Tokyo": {"temperature": "18°C", "description": "Light rain"},
            "Paris": {"temperature": "17°C", "description": "Overcast"},
            "Sydney": {"temperature": "25°C", "description": "Clear sky"},
            "Mumbai": {"temperature": "32°C", "description": "Hot and humid"},
            "Toronto": {"temperature": "12°C", "description": "Windy"},
            "Berlin": {"temperature": "14°C", "description": "Cloudy"},
            "Moscow": {"temperature": "8°C", "description": "Cold and clear"},
            "Dubai": {"temperature": "38°C", "description": "Very hot"},
        }
    
    def get_weather(self, city: str) -> Optional[Dict[str, str]]:
        """Get weather data for a specific city.
        
        Args:
            city: Name of the city
            
        Returns:
            Dictionary with 'temperature' and 'description' keys, or None if city not found
        """
        # Case-insensitive city lookup
        for key, data in self._weather_data.items():
            if key.lower() == city.lower():
                return data
        return None
    
    def get_available_cities(self) -> list[str]:
        """Get list of available cities.
        
        Returns:
            List of city names with weather data available
        """
        return sorted(list(self._weather_data.keys()))