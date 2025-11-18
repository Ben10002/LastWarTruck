from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db


class User(UserMixin, db.Model):
    """User Model - User accounts"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)  # For account suspension
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    subscription = db.relationship('Subscription', backref='user', uselist=False, cascade='all, delete-orphan')
    bot_config = db.relationship('BotConfig', backref='user', uselist=False, cascade='all, delete-orphan')
    bot_timers = db.relationship('BotTimer', backref='user', cascade='all, delete-orphan')
    bot_logs = db.relationship('BotLog', backref='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    @property
    def has_active_subscription(self):
        """Check if user has an active subscription"""
        if not self.subscription:
            return False
        return self.subscription.is_active
    
    def __repr__(self):
        return f'<User {self.email}>'