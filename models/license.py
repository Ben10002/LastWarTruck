from datetime import datetime, timedelta
from . import db
import secrets
import string


class License(db.Model):
    """License keys for users"""
    __tablename__ = 'licenses'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    duration_days = db.Column(db.Integer, nullable=False)
    is_redeemed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    redeemed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('licenses', lazy='dynamic'))
    
    def __repr__(self):
        return f'<License {self.key}>'
    
    @staticmethod
    def generate_key():
        """Generate a random license key (format: XXXX-XXXX-XXXX-XXXX)"""
        chars = string.ascii_uppercase + string.digits
        key = '-'.join(''.join(secrets.choice(chars) for _ in range(4)) for _ in range(4))
        return key
    
    def redeem(self, user):
        """Redeem license key for a user"""
        if self.is_redeemed:
            return False
        
        self.is_redeemed = True
        self.user_id = user.id
        self.redeemed_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=self.duration_days)
        
        # Update or create user subscription
        from .subscription import Subscription
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if subscription:
            # Extend existing subscription using the extend method
            subscription.extend(self.duration_days)
        else:
            # Create new subscription
            subscription = Subscription(
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=self.duration_days)
            )
            db.session.add(subscription)
        
        return True
    
    @property
    def is_valid(self):
        """Check if license is still valid"""
        if not self.is_redeemed:
            return True
        return self.expires_at and self.expires_at > datetime.utcnow()
    
    @property
    def status(self):
        """Get license status"""
        if not self.is_redeemed:
            return 'Available'
        elif self.is_valid:
            return 'Active'
        else:
            return 'Expired'