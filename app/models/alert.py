from app import db
from datetime import datetime, timedelta
import requests
from flask import current_app

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Integer)
    wind_speed = db.Column(db.Float)

    def __init__(self, **kwargs):
        super(Alert, self).__init__(**kwargs)
        if not self.expires_at:
            self.expires_at = datetime.utcnow() + timedelta(days=1)
        
        # Verify weather data for weather alerts
        if self.alert_type == 'weather' and self.location:
            self.verify_weather()

    def verify_weather(self):
        """Verify weather conditions for the alert location"""
        try:
            api_key = current_app.config['OPENWEATHER_API_KEY']
            
            # If location is coordinates
            if ',' in self.location:
                lat, lon = map(float, self.location.split(','))
            else:
                # Use OpenWeatherMap Geocoding API
                geo_url = "http://api.openweathermap.org/geo/1.0/direct"
                geo_params = {
                    'q': self.location,
                    'limit': 1,
                    'appid': api_key
                }
                
                geo_response = requests.get(geo_url, params=geo_params)
                geo_data = geo_response.json()
                
                if not geo_data:
                    return
                    
                lat = geo_data[0]['lat']
                lon = geo_data[0]['lon']

            # Get weather data
            weather_url = "http://api.openweathermap.org/data/2.5/weather"
            weather_params = {
                'lat': lat,
                'lon': lon,
                'units': 'metric',
                'appid': api_key
            }

            weather_response = requests.get(weather_url, params=weather_params)
            weather_data = weather_response.json()

            if weather_data.get('cod') == 200:
                self.temperature = weather_data['main']['temp']
                self.humidity = weather_data['main']['humidity']
                self.wind_speed = weather_data['wind']['speed'] * 3.6  # Convert m/s to km/h

                # Update severity based on weather conditions
                if self.temperature >= 40:  # Extreme heat
                    self.severity = 'critical'
                elif self.temperature >= 35:  # High heat
                    self.severity = 'high'
                elif self.temperature <= -10:  # Extreme cold
                    self.severity = 'critical'
                elif self.temperature <= 0:  # Cold
                    self.severity = 'high'
                
                # Update description with weather details
                weather_details = f"\n\nWeather Details:\nTemperature: {round(self.temperature)}°C\n"
                weather_details += f"Humidity: {self.humidity}%\n"
                weather_details += f"Wind Speed: {round(self.wind_speed, 1)} km/h"
                
                if not self.description.endswith(weather_details):
                    self.description += weather_details

        except Exception as e:
            print(f"Error verifying weather: {str(e)}")

    def __repr__(self):
        return f'<Alert {self.title}>' 