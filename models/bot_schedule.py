from datetime import datetime, time
from . import db


class BotSchedule(db.Model):
    """BotSchedule Model - Automated bot scheduling per user"""
    
    __tablename__ = 'bot_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Schedule Name
    name = db.Column(db.String(100), nullable=False)
    
    # Day of week (0=Monday, 6=Sunday) - NULL means every day
    day_of_week = db.Column(db.Integer, nullable=True)
    
    # Time settings
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Bot settings for this schedule
    share_alliance = db.Column(db.Boolean, default=True)
    share_world = db.Column(db.Boolean, default=False)
    truck_strength = db.Column(db.Integer, default=30)
    server_restriction_enabled = db.Column(db.Boolean, default=False)
    server_restriction_value = db.Column(db.Integer, nullable=True)
    
    # Schedule status
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('bot_schedules', lazy='dynamic'))
    
    def __repr__(self):
        return f'<BotSchedule {self.name} - {self.start_time} to {self.end_time}>'
    
    def overlaps_with(self, other_schedule):
        """Check if this schedule overlaps with another schedule"""
        # Same day or both are daily schedules
        if self.day_of_week == other_schedule.day_of_week or \
           self.day_of_week is None or other_schedule.day_of_week is None:
            # Check time overlap
            return (self.start_time < other_schedule.end_time and 
                    self.end_time > other_schedule.start_time)
        return False
    
    @property
    def day_name(self):
        """Get human-readable day name"""
        if self.day_of_week is None:
            return "Every Day"
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return days[self.day_of_week]