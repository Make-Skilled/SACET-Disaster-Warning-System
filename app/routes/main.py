from flask import Blueprint, render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.models.alert import Alert
from app.models.user import User
from app.models.helpline import Helpline
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
import math

bp = Blueprint('main', __name__)

def get_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers

    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

@bp.route('/')
def index():
    alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).limit(5).all()
    helplines = Helpline.query.filter_by(is_active=True).all()
    
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    return render_template('index.html', alerts=alerts, helplines=helplines)

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get alert counts
    active_alerts = Alert.query.filter_by(is_active=True).count()
    critical_alerts = Alert.query.filter_by(severity='critical', is_active=True).count()
    weather_alerts = Alert.query.filter_by(alert_type='weather', is_active=True).count()

    # Get nearby alerts based on user's location
    nearby_alerts = []
    if current_user.location:
        try:
            user_lat, user_lon = map(float, current_user.location.split(','))
            all_alerts = Alert.query.filter_by(is_active=True).all()
            
            for alert in all_alerts:
                try:
                    alert_lat, alert_lon = map(float, alert.location.split(','))
                    distance = get_distance(user_lat, user_lon, alert_lat, alert_lon)
                    
                    if distance <= current_user.alert_radius:
                        nearby_alerts.append(alert)
                except ValueError:
                    continue
        except ValueError:
            pass

    # Get all active alerts for display
    alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).all()
    
    # Get active helplines
    helplines = Helpline.query.filter_by(is_active=True).all()

    return render_template('dashboard/user_dashboard.html',
                         active_alerts=active_alerts,
                         critical_alerts=critical_alerts,
                         weather_alerts=weather_alerts,
                         nearby_alerts=nearby_alerts,
                         alerts=alerts,
                         helplines=helplines)

@bp.route('/helplines')
def helplines():
    helplines = Helpline.query.filter_by(is_active=True).all()
    return render_template('main/helplines.html', helplines=helplines)

@bp.route('/api/alerts/search')
@login_required
def search_alerts():
    location = request.args.get('location')
    radius = float(request.args.get('radius', 50))
    alert_type = request.args.get('alert_type')

    if not location:
        return {'alerts': []}

    try:
        lat, lon = map(float, location.split(','))
    except ValueError:
        # If location is not coordinates, try to geocode it
        try:
            response = current_app.geocoder.geocode(location)
            if not response:
                return {'alerts': []}
            lat, lon = response.latitude, response.longitude
        except Exception as e:
            current_app.logger.error(f"Geocoding error: {e}")
            return {'alerts': []}

    # Get all active alerts
    query = Alert.query.filter_by(is_active=True)
    
    # Filter by alert type if specified
    if alert_type:
        query = query.filter_by(alert_type=alert_type)

    # Get all alerts and filter by distance
    alerts = []
    for alert in query.all():
        try:
            alert_lat, alert_lon = map(float, alert.location.split(','))
            distance = get_distance(lat, lon, alert_lat, alert_lon)
            
            if distance <= radius:
                alert_dict = {
                    'id': alert.id,
                    'title': alert.title,
                    'description': alert.description,
                    'severity': alert.severity,
                    'alert_type': alert.alert_type,
                    'location': alert.location,
                    'created_at': alert.created_at.isoformat(),
                    'distance': round(distance, 1)
                }
                
                if alert.alert_type == 'weather':
                    alert_dict.update({
                        'temperature': alert.temperature,
                        'humidity': alert.humidity,
                        'wind_speed': alert.wind_speed
                    })
                
                alerts.append(alert_dict)
        except ValueError:
            continue

    # Sort alerts by distance
    alerts.sort(key=lambda x: x['distance'])
    
    return {'alerts': alerts} 