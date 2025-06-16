# Weather CLI

## Project Overview
A command-line weather application that fetches and displays weather information

## Success Criteria
- Fetch weather data for any city
- Display current temperature and conditions
- Cache results to avoid repeated API calls
- All tests pass

## Milestones

### Milestone 1: Basic weather fetching
- Create WeatherClient class that simulates API calls (hardcoded data for now)
- Implement get_weather(city) method returning temperature and description
- Create CLI with menu: Check Weather, List Cities, Exit
- Display weather in a nice format
- main.py runs successfully

### Milestone 2: Add caching system
- Implement CacheManager class to store weather data
- Cache weather results for 30 minutes
- Add cache status to weather display (cached/fresh)
- Add "Clear Cache" option to menu
- Save cache to weather_cache.json
- Ensure main.py still works with all features