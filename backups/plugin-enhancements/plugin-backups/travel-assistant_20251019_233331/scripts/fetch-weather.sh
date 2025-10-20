#!/bin/bash
# Fetch weather data from OpenWeatherMap API
# Usage: ./fetch-weather.sh "location"

LOCATION="${1:-London}"
API_KEY="${OPENWEATHER_API_KEY:-demo}"  # User should set their own key

# Free tier OpenWeatherMap API (1000 calls/day)
curl -s "https://api.openweathermap.org/data/2.5/forecast?q=${LOCATION}&appid=${API_KEY}&units=metric" 2>/dev/null || echo '{"error":"API unavailable, using mock data"}'
