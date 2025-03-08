from app import db
from datetime import datetime

class Helpline(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), nullable=False)  # e.g., 'emergency', 'medical', 'fire', 'police'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Helpline {self.name}>' 