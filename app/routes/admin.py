from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.alert import Alert
from app.models.activity_log import ActivityLog
from app.models.helpline import Helpline
from app import db
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import func
import requests
import os

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def create_default_helplines():
    default_helplines = [
        {
            'name': 'National Emergency Number',
            'number': '112',
            'category': 'emergency',
            'description': '24/7 National Emergency Services'
        },
        {
            'name': 'Ambulance Services',
            'number': '108',
            'category': 'medical',
            'description': '24/7 Ambulance & Medical Emergency'
        },
        {
            'name': 'Fire & Rescue',
            'number': '101',
            'category': 'fire',
            'description': 'Fire Brigade & Rescue Services'
        },
        {
            'name': 'Police Control Room',
            'number': '100',
            'category': 'police',
            'description': 'Police Emergency Services'
        },
        {
            'name': 'Women Helpline',
            'number': '1091',
            'category': 'emergency',
            'description': 'Women Safety & Emergency Support'
        },
        {
            'name': 'Child Helpline',
            'number': '1098',
            'category': 'emergency',
            'description': 'Child Safety & Support'
        },
        {
            'name': 'Disaster Management',
            'number': '1070',
            'category': 'disaster',
            'description': 'National Disaster Response Force'
        },
        {
            'name': 'COVID-19 Helpline',
            'number': '1075',
            'category': 'medical',
            'description': 'COVID-19 Related Emergency Support'
        }
    ]

    try:
        for helpline_data in default_helplines:
            existing = Helpline.query.filter_by(number=helpline_data['number']).first()
            if not existing:
                helpline = Helpline(
                    name=helpline_data['name'],
                    number=helpline_data['number'],
                    category=helpline_data['category'],
                    description=helpline_data['description'],
                    is_active=True
                )
                db.session.add(helpline)
        
        db.session.commit()
        print("Default helplines created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default helplines: {str(e)}")

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_alerts = Alert.query.count()
    active_alerts = Alert.query.filter_by(is_active=True).count()
    total_users = User.query.count()
    critical_alerts = Alert.query.filter_by(severity='critical', is_active=True).count()
    
    recent_alerts = Alert.query.order_by(Alert.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         total_alerts=total_alerts,
                         active_alerts=active_alerts,
                         total_users=total_users,
                         critical_alerts=critical_alerts,
                         recent_alerts=recent_alerts)

@bp.route('/manage-alerts')
@login_required
@admin_required
def manage_alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).all()
    return render_template('admin/manage_alerts.html', alerts=alerts)

@bp.route('/create-alert', methods=['GET', 'POST'])
@login_required
@admin_required
def create_alert():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        alert_type = request.form['alert_type']
        severity = request.form['severity']
        location = request.form['location']

        alert = Alert(
            title=title,
            description=description,
            alert_type=alert_type,
            severity=severity,
            location=location,
            created_by=current_user.id
        )

        if alert_type == 'weather':
            # Fetch weather data from API
            try:
                weather_url = "http://api.openweathermap.org/data/2.5/weather"
                try:
                    lat, lon = map(float, location.split(','))
                    params = {'lat': lat, 'lon': lon}
                except ValueError:
                    params = {'q': location}
                
                params.update({
                    'appid': os.getenv('OPENWEATHER_API_KEY'),
                    'units': 'metric'
                })
                
                response = requests.get(weather_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    alert.temperature = data['main']['temp']
                    alert.humidity = data['main']['humidity']
                    alert.wind_speed = data['wind']['speed'] * 3.6  # Convert m/s to km/h
                    
                    # Update severity based on temperature
                    if alert.temperature >= 40 or alert.temperature <= -10:
                        alert.severity = 'critical'
                    elif alert.temperature >= 35 or alert.temperature <= 0:
                        alert.severity = 'high'
                    elif alert.temperature >= 30 or alert.temperature <= 5:
                        alert.severity = 'medium'
                    else:
                        alert.severity = 'low'
            except Exception as e:
                flash(f'Error fetching weather data: {str(e)}', 'error')

        db.session.add(alert)
        db.session.commit()
        flash('Alert created successfully!', 'success')
        return redirect(url_for('admin.manage_alerts'))

    return render_template('admin/create_alert.html')

@bp.route('/edit-alert/<int:alert_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    
    if request.method == 'POST':
        alert.title = request.form['title']
        alert.description = request.form['description']
        alert.location = request.form['location']
        alert.is_active = 'is_active' in request.form
        
        # Only update alert_type if it's not a weather alert
        if alert.alert_type != 'weather':
            alert.alert_type = request.form['alert_type']
            alert.severity = request.form['severity']
        else:
            # For weather alerts, update weather data
            alert.temperature = request.form.get('temperature', type=float)
            alert.humidity = request.form.get('humidity', type=float)
            alert.wind_speed = request.form.get('wind_speed', type=float)
            
            # Update severity based on weather conditions
            if alert.temperature > 40:
                alert.severity = 'critical'
            elif alert.temperature > 35:
                alert.severity = 'high'
            elif alert.temperature > 30:
                alert.severity = 'medium'
            else:
                alert.severity = 'low'
        
        try:
            db.session.commit()
            flash('Alert updated successfully!', 'success')
            return redirect(url_for('admin.manage_alerts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating alert: {str(e)}', 'error')
    
    return render_template('admin/edit_alert.html', alert=alert)

@bp.route('/delete-alert/<int:alert_id>')
@login_required
@admin_required
def delete_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    db.session.delete(alert)
    db.session.commit()
    flash('Alert deleted successfully!', 'success')
    return redirect(url_for('admin.manage_alerts'))

@bp.route('/helplines')
@login_required
@admin_required
def helplines():
    helplines = Helpline.query.all()
    return render_template('admin/helplines.html', helplines=helplines)

@bp.route('/create-helpline', methods=['GET', 'POST'])
@login_required
@admin_required
def create_helpline():
    if request.method == 'POST':
        name = request.form['name']
        number = request.form['number']
        description = request.form['description']
        category = request.form['category']

        helpline = Helpline(
            name=name,
            number=number,
            description=description,
            category=category
        )

        db.session.add(helpline)
        db.session.commit()
        flash('Helpline added successfully!', 'success')
        return redirect(url_for('admin.helplines'))

    return render_template('admin/create_helpline.html')

@bp.route('/edit-helpline/<int:helpline_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_helpline(helpline_id):
    helpline = Helpline.query.get_or_404(helpline_id)
    
    if request.method == 'POST':
        helpline.name = request.form['name']
        helpline.number = request.form['number']
        helpline.description = request.form['description']
        helpline.category = request.form['category']
        
        db.session.commit()
        flash('Helpline updated successfully!', 'success')
        return redirect(url_for('admin.helplines'))
    
    return render_template('admin/edit_helpline.html', helpline=helpline)

@bp.route('/delete-helpline/<int:helpline_id>')
@login_required
@admin_required
def delete_helpline(helpline_id):
    helpline = Helpline.query.get_or_404(helpline_id)
    db.session.delete(helpline)
    db.session.commit()
    flash('Helpline deleted successfully!', 'success')
    return redirect(url_for('admin.helplines'))

@bp.route('/alert-stats')
@login_required
@admin_required
def alert_stats():
    # Get alert type distribution
    alert_types = db.session.query(Alert.alert_type, func.count(Alert.id))\
        .group_by(Alert.alert_type).all()
    alert_type_labels = [t[0].capitalize() for t in alert_types]
    alert_type_counts = [t[1] for t in alert_types]

    # Get severity distribution
    severity_data = db.session.query(Alert.severity, func.count(Alert.id))\
        .group_by(Alert.severity).all()
    severity_levels = [s[0].capitalize() for s in severity_data]
    severity_counts = [s[1] for s in severity_data]

    # Get temperature trends for weather alerts
    last_week = datetime.now() - timedelta(days=7)
    temp_data = db.session.query(
        Alert.created_at,
        Alert.temperature
    ).filter(
        Alert.alert_type == 'weather',
        Alert.created_at >= last_week,
        Alert.temperature.isnot(None)
    ).order_by(Alert.created_at).all()

    temp_dates = [t[0].strftime('%Y-%m-%d') for t in temp_data]
    temperatures = [float(t[1]) for t in temp_data if t[1] is not None]

    # Get alert activity timeline
    activity_data = db.session.query(
        Alert.created_at,
        func.count(Alert.id)
    ).group_by(
        func.date(Alert.created_at)
    ).order_by(
        Alert.created_at.desc()
    ).limit(30).all()

    activity_dates = [d[0].strftime('%Y-%m-%d') for d in activity_data]
    activity_counts = [d[1] for d in activity_data]

    # Calculate additional statistics
    total_alerts = sum(alert_type_counts)
    active_alerts = Alert.query.filter_by(is_active=True).count()
    critical_alerts = Alert.query.filter_by(severity='critical', is_active=True).count()
    weather_alerts = Alert.query.filter_by(alert_type='weather', is_active=True).count()

    return render_template('admin/alert_stats.html',
                         alert_types=alert_type_labels,
                         alert_type_counts=alert_type_counts,
                         severity_levels=severity_levels,
                         severity_counts=severity_counts,
                         temp_dates=temp_dates,
                         temperatures=temperatures,
                         activity_dates=activity_dates,
                         activity_counts=activity_counts,
                         total_alerts=total_alerts,
                         active_alerts=active_alerts,
                         critical_alerts=critical_alerts,
                         weather_alerts=weather_alerts)

@bp.route('/location-analysis')
@login_required
@admin_required
def location_analysis():
    alerts = Alert.query.all()
    return render_template('admin/location_analysis.html', alerts=alerts)

@bp.route('/response-metrics')
@login_required
@admin_required
def response_metrics():
    return render_template('admin/response_metrics.html')

@bp.route('/notification-settings')
@login_required
@admin_required
def notification_settings():
    return render_template('admin/notification_settings.html')

@bp.route('/security-settings')
@login_required
@admin_required
def security_settings():
    return render_template('admin/security_settings.html')

@bp.route('/system-logs')
@login_required
@admin_required
def system_logs():
    return render_template('admin/system_logs.html')

@bp.route('/manage-users')
@login_required
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

@bp.route('/user-activity')
@login_required
@admin_required
def user_activity():
    activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).all()
    return render_template('admin/user_activity.html', activities=activities)

@bp.route('/manage-roles')
@login_required
@admin_required
def manage_roles():
    users = User.query.all()
    return render_template('admin/manage_roles.html', users=users)

def create_sample_users():
    sample_users = [
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'password': 'user123',
            'is_admin': False,
            'location': 'New York',
            'phone': '+1234567890'
        },
        {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'password': 'user123',
            'is_admin': False,
            'location': 'Los Angeles',
            'phone': '+1987654321'
        },
        {
            'username': 'bob_wilson',
            'email': 'bob@example.com',
            'password': 'user123',
            'is_admin': False,
            'location': 'Chicago',
            'phone': '+1122334455'
        }
    ]

    try:
        for user_data in sample_users:
            existing = User.query.filter_by(email=user_data['email']).first()
            if not existing:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    is_admin=user_data['is_admin'],
                    location=user_data['location'],
                    phone=user_data['phone']
                )
                user.set_password(user_data['password'])
                db.session.add(user)
        
        db.session.commit()
        print("Sample users created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample users: {str(e)}")

@bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.location = request.form['location']
        user.phone = request.form['phone']
        user.email_alerts = 'email_alerts' in request.form
        user.sms_alerts = 'sms_alerts' in request.form
        
        if request.form.get('new_password'):
            user.set_password(request.form['new_password'])
        
        try:
            db.session.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('admin.manage_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@bp.route('/delete-user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot delete admin user!', 'error')
        return redirect(url_for('admin.manage_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users')) 