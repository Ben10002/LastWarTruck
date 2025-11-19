from datetime import datetime
from . import db


class BotConfig(db.Model):
    """BotConfig Model - Bot & VMOSCloud settings per user"""
    
    __tablename__ = 'bot_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # VMOSCloud SSH Connection (Admin-managed)
    ssh_host = db.Column(db.String(255), nullable=True)
    ssh_port = db.Column(db.Integer, default=22)
    ssh_user = db.Column(db.String(100), nullable=True)
    ssh_pass = db.Column(db.String(255), nullable=True)  # Encrypt in production!
    adb_port = db.Column(db.Integer, default=5555)
    
    # Screen Settings (Admin-managed)
    screen_width = db.Column(db.Integer, default=720)
    screen_height = db.Column(db.Integer, default=1280)
    
    # Bot Settings (User-configurable)
    share_alliance = db.Column(db.Boolean, default=False)  # Share in Alliance
    share_world = db.Column(db.Boolean, default=False)  # Share in World Chat (mutually exclusive)
    truck_strength = db.Column(db.Integer, default=30)  # Truck strength in millions
    server_restriction_enabled = db.Column(db.Boolean, default=False)  # Enable server restriction
    server_restriction_value = db.Column(db.Integer, nullable=True)  # Server number restriction
    running_timer_minutes = db.Column(db.Integer, default=60)  # Total runtime before auto-stop
    remember_trucks_hours = db.Column(db.Integer, default=1)  # Remember saved trucks (default 1h)
    
    # Bot Status
    is_running = db.Column(db.Boolean, default=False)
    last_started = db.Column(db.DateTime, nullable=True)
    last_stopped = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_configured(self):
        """Check if bot is fully configured (by admin)"""
        return all([
            self.ssh_host,
            self.ssh_user,
            self.ssh_pass
        ])
    
    def to_dict(self):
        """Convert to dictionary for bot"""
        return {
            'ssh_host': self.ssh_host,
            'ssh_port': self.ssh_port,
            'ssh_user': self.ssh_user,
            'ssh_pass': self.ssh_pass,
            'adb_port': self.adb_port,
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'running_timer_minutes': self.running_timer_minutes,
            'share_alliance': self.share_alliance,
            'share_world': self.share_world,
            'truck_strength': self.truck_strength,
            'server_restriction_enabled': self.server_restriction_enabled,
            'server_restriction_value': self.server_restriction_value,
            'remember_trucks_hours': self.remember_trucks_hours
        }
    
    def __repr__(self):
        return f'<BotConfig user_id={self.user_id} configured={self.is_configured}>'


class BotTimer(db.Model):
    """BotTimer Model - Persistent timers per user"""
    
    __tablename__ = 'bot_timers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timer_name = db.Column(db.String(50), nullable=False)  # e.g. 'lkw_1', 'lkw_2', etc.
    next_run = db.Column(db.DateTime, nullable=False)
    interval_seconds = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: A user can only have one timer with the same name
    __table_args__ = (
        db.UniqueConstraint('user_id', 'timer_name', name='unique_user_timer'),
    )
    
    @property
    def is_ready(self):
        """Check if timer is ready to execute"""
        return datetime.utcnow() >= self.next_run and self.is_active
    
    def reset(self):
        """Reset timer (next run = now + interval)"""
        from datetime import timedelta
        self.next_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<BotTimer {self.timer_name} next={self.next_run}>'


class BotLog(db.Model):
    """BotLog Model - Log entries per user"""
    
    __tablename__ = 'bot_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    log_type = db.Column(db.String(20), nullable=False)  # 'info', 'success', 'warning', 'error'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<BotLog [{self.log_type}] {self.message[:50]}>'
    
    @staticmethod
    def add_log(user_id, log_type, message):
        """Add new log entry"""
        log = BotLog(
            user_id=user_id,
            log_type=log_type,
            message=message
        )
        db.session.add(log)
        db.session.commit()
    
    @staticmethod
    def get_recent_logs(user_id, limit=50):
        """Get the most recent logs for a user"""
        return BotLog.query.filter_by(user_id=user_id)\
                          .order_by(BotLog.created_at.desc())\
                          .limit(limit)\
                          .all()
    
    @staticmethod
    def clear_old_logs(days=7):
        """Delete logs older than X days"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        BotLog.query.filter(BotLog.created_at < cutoff).delete()
        db.session.commit()