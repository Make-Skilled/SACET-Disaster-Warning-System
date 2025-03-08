from flask import Blueprint, jsonify, request
import requests
from math import radians, sin, cos, sqrt, atan2
import os

bp = Blueprint('api', __name__, url_prefix='/api')

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

@bp.route('/weather')
def get_weather():
    location = request.args.get('location', '')
    if not location:
        return jsonify({'error': 'Location is required'})

    # If location is coordinates (lat,lon)
    if ',' in location:
        lat, lon = map(float, location.split(','))
    else:
        # Use OpenWeatherMap Geocoding API to get coordinates
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct"
        geo_params = {
            'q': location,
            'limit': 1,
            'appid': os.getenv('OPENWEATHER_API_KEY', 'your-api-key')
        }
        
        try:
            geo_response = requests.get(geo_url, params=geo_params)
            geo_data = geo_response.json()
            
            if not geo_data:
                return jsonify({'error': 'Location not found'})
                
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
        except Exception as e:
            return jsonify({'error': f'Error getting location coordinates: {str(e)}'})

    # Get weather data from OpenWeatherMap
    weather_url = f"http://api.openweathermap.org/data/2.5/weather"
    weather_params = {
        'lat': lat,
        'lon': lon,
        'units': 'metric',
        'appid': os.getenv('OPENWEATHER_API_KEY', 'your-api-key')
    }

    try:
        weather_response = requests.get(weather_url, params=weather_params)
        weather_data = weather_response.json()

        if weather_data.get('cod') != 200:
            return jsonify({'error': weather_data.get('message', 'Error fetching weather data')})

        return jsonify({
            'temperature': round(weather_data['main']['temp']),
            'description': weather_data['weather'][0]['description'].capitalize(),
            'humidity': weather_data['main']['humidity'],
            'wind_speed': round(weather_data['wind']['speed'] * 3.6, 1),  # Convert m/s to km/h
            'icon': f"http://openweathermap.org/img/w/{weather_data['weather'][0]['icon']}.png"
        })

    except Exception as e:
        return jsonify({'error': f'Error fetching weather data: {str(e)}'}) 