from app import db
from datetime import datetime

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    activity_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45), nullable=True)
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    
    @staticmethod
    def log_activity(user_id, activity_type, description, ip_address=None, 
                    resource_type=None, resource_id=None, status=None):
        """
        Create and save a new activity log entry.
        
        Args:
            user_id (int): ID of the user performing the activity
            activity_type (str): Type of activity (e.g., 'login', 'create_alert', etc.)
            description (str): Description of the activity
            ip_address (str, optional): IP address of the user
            resource_type (str, optional): Type of resource being acted upon
            resource_id (int, optional): ID of the resource being acted upon
            status (str, optional): Status of the activity
        """
        log = ActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status
        )
        db.session.add(log)
        db.session.commit()
        
    def __repr__(self):
        return f'<ActivityLog {self.activity_type} by User {self.user_id} at {self.timestamp}>' 