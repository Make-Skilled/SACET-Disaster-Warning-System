from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from config import Config
import os
from datetime import datetime, timedelta

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)
    csrf.init_app(app)
    
    # Import models to ensure they are registered with SQLAlchemy
    from app.models.user import User
    from app.models.alert import Alert
    
    def create_sample_alerts():
        # Get admin user for created_by field
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            return
            
        sample_alerts = [
            {
                'title': 'Severe Cyclone Warning',
                'description': 'Category 4 cyclone approaching the eastern coast. Expected landfall within 48 hours. Wind speeds up to 200 km/h.',
                'alert_type': 'weather',
                'severity': 'critical',
                'location': 'Eastern Coastal Region',
                'created_at': datetime.now() - timedelta(days=5),
                'temperature': 27.5,
                'humidity': 85,
                'wind_speed': 200,
                'is_active': True
            },
            {
                'title': 'Flood Alert',
                'description': 'Heavy rainfall has caused river levels to rise significantly. Residents in low-lying areas should evacuate.',
                'alert_type': 'natural',
                'severity': 'high',
                'location': 'Riverside District',
                'created_at': datetime.now() - timedelta(days=3),
                'is_active': True
            },
            {
                'title': 'Extreme Heat Warning',
                'description': 'Temperature expected to reach 42°C. Stay hydrated and avoid outdoor activities.',
                'alert_type': 'weather',
                'severity': 'critical',
                'location': 'Central Region',
                'created_at': datetime.now() - timedelta(days=2),
                'temperature': 42,
                'humidity': 30,
                'wind_speed': 15,
                'is_active': True
            },
            {
                'title': 'Forest Fire Alert',
                'description': 'Large forest fire spreading in the northern woods. Nearby residents should prepare for possible evacuation.',
                'alert_type': 'fire',
                'severity': 'high',
                'location': 'Northern Forest Area',
                'created_at': datetime.now() - timedelta(days=1),
                'is_active': True
            },
            {
                'title': 'Public Health Advisory',
                'description': 'Increased cases of seasonal flu reported. Take necessary precautions and maintain hygiene.',
                'alert_type': 'health',
                'severity': 'medium',
                'location': 'City-wide',
                'created_at': datetime.now() - timedelta(hours=12),
                'is_active': True
            }
        ]

        try:
            for alert_data in sample_alerts:
                existing = Alert.query.filter_by(
                    title=alert_data['title'],
                    created_at=alert_data['created_at']
                ).first()
                
                if not existing:
                    alert = Alert(
                        title=alert_data['title'],
                        description=alert_data['description'],
                        alert_type=alert_data['alert_type'],
                        severity=alert_data['severity'],
                        location=alert_data['location'],
                        created_at=alert_data['created_at'],
                        created_by=admin_user.id,
                        is_active=alert_data['is_active']
                    )
                    if alert_data['alert_type'] == 'weather':
                        alert.temperature = alert_data['temperature']
                        alert.humidity = alert_data['humidity']
                        alert.wind_speed = alert_data['wind_speed']
                    
                    db.session.add(alert)
            
            db.session.commit()
            print("Sample alerts created successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating sample alerts: {str(e)}")
    
    # Register blueprints
    from app.routes import main, auth, alerts, admin, api
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(api.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@system.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@system.com',
                is_admin=True,
                email_alerts=True,
                alert_radius=50
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
        
        # Create default helplines
        from app.routes.admin import create_default_helplines, create_sample_users
        create_default_helplines()
        
        # Create sample users
        create_sample_users()
        
        # Create sample alerts
        create_sample_alerts()
    
    return app 