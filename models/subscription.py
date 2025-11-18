from datetime import datetime, timedelta
import secrets
from . import db


class Subscription(db.Model):
    """Subscription Model - Subscription status per user"""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_active(self):
        """Check if subscription is still active"""
        return datetime.utcnow() < self.expires_at
    
    @property
    def days_remaining(self):
        """Calculate remaining days"""
        if not self.is_active:
            return 0
        delta = self.expires_at - datetime.utcnow()
        return delta.days
    
    def extend(self, days):
        """Extend subscription by X days"""
        if self.is_active:
            # Subscription is still active -> extend from current expiry date
            self.expires_at += timedelta(days=days)
        else:
            # Subscription has expired -> extend from now
            self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Subscription user_id={self.user_id} expires={self.expires_at}>'


class LicenseKey(db.Model):
    """LicenseKey Model - Redeemable keys"""
    
    __tablename__ = 'license_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    key_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    duration_days = db.Column(db.Integer, nullable=False)  # Duration in days
    is_redeemed = db.Column(db.Boolean, default=False)
    redeemed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    redeemed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Admin who created the key
    
    @staticmethod
    def generate_key():
        """Generate a random key (Format: XXXX-XXXX-XXXX-XXXX)"""
        parts = []
        for _ in range(4):
            parts.append(secrets.token_hex(2).upper())
        return '-'.join(parts)
    
    def redeem(self, user_id):
        """Redeem key for a user"""
        if self.is_redeemed:
            return False, "Key has already been redeemed"
        
        self.is_redeemed = True
        self.redeemed_by = user_id
        self.redeemed_at = datetime.utcnow()
        
        # Extend user's subscription
        from .user import User
        user = User.query.get(user_id)
        
        if not user.subscription:
            # Create new subscription
            subscription = Subscription(
                user_id=user_id,
                expires_at=datetime.utcnow() + timedelta(days=self.duration_days)
            )
            db.session.add(subscription)
        else:
            # Extend existing subscription
            user.subscription.extend(self.duration_days)
        
        db.session.commit()
        return True, f"Key successfully redeemed! {self.duration_days} days added."
    
    def __repr__(self):
        return f'<LicenseKey {self.key_code} ({self.duration_days} days)>'