from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models.alert import Alert
from app import db
from datetime import datetime

bp = Blueprint('alerts', __name__)

@bp.route('/alerts')
@login_required
def alerts():
    alerts = Alert.query.filter_by(is_active=True).order_by(Alert.created_at.desc()).all()
    return render_template('alerts/alerts.html', alerts=alerts)

@bp.route('/alerts/create', methods=['GET', 'POST'])
@login_required
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
            alert.temperature = float(request.form.get('temperature', 0))
            alert.humidity = float(request.form.get('humidity', 0))
            alert.wind_speed = float(request.form.get('wind_speed', 0))

        db.session.add(alert)
        db.session.commit()

        flash('Alert created successfully!', 'success')
        return redirect(url_for('alerts.alerts'))

    return render_template('alerts/create_alert.html') 