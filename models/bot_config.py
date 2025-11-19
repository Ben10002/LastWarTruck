from datetime import datetime, timedelta
from . import db


class BotConfig(db.Model):
    """BotConfig Model - User's bot configuration and settings"""
    
    __tablename__ = 'bot_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # VMOSCloud SSH Connection (Admin-managed)
    ssh_command = db.Column(db.Text, nullable=True)  # Full SSH command from VMOSCloud
    ssh_key = db.Column(db.Text, nullable=True)  # Connection key (base64)
    
    # Parsed from ssh_command (auto-filled)
    ssh_host = db.Column(db.String(255), nullable=True)
    ssh_port = db.Column(db.Integer, default=22)
    ssh_username = db.Column(db.String(255), nullable=True)
    adb_proxy_port = db.Column(db.Integer, nullable=True)
    local_adb_port = db.Column(db.Integer, default=7071)
    
    # Screen resolution
    screen_width = db.Column(db.Integer, default=720)
    screen_height = db.Column(db.Integer, default=1280)
    
    # Bot Settings (User-configurable)
    share_alliance = db.Column(db.Boolean, default=True)  # Share in Alliance (DEFAULT: ON)
    share_world = db.Column(db.Boolean, default=False)  # Share in World Chat
    truck_strength = db.Column(db.Integer, default=30)  # Truck strength limit in millions (DEFAULT: 30M)
    server_restriction_enabled = db.Column(db.Boolean, default=False)  # Enable server restriction (DEFAULT: OFF)
    server_restriction_value = db.Column(db.Integer, nullable=True)  # Server number restriction
    running_timer_enabled = db.Column(db.Boolean, default=False)  # Enable auto-stop timer (DEFAULT: OFF)
    running_timer_minutes = db.Column(db.Integer, default=60)  # Auto-stop timer in minutes
    remember_trucks_hours = db.Column(db.Integer, default=1)  # Remember saved trucks (default 1h)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('bot_config', uselist=False))
    
    @property
    def is_configured(self):
        """Check if bot is fully configured (by admin)"""
        return all([
            self.ssh_host,
            self.ssh_port,
            self.ssh_username,
            self.ssh_key,
            self.adb_proxy_port
        ])
    
    def parse_ssh_command(self):
        """Parse SSH command and extract connection details"""
        if not self.ssh_command:
            return False
        
        import re
        
        # Example: ssh -oHostKeyAlgorithms=+ssh-rsa 10.0.8.67_1763575271849@103.237.100.130 -p 1824 -L 7071:adb-proxy:39131 -Nf
        
        # Extract username@host
        username_match = re.search(r'\s+([^\s]+@[0-9.]+)\s+-p', self.ssh_command)
        if username_match:
            full_username = username_match.group(1)
            self.ssh_username = full_username
            # Extract host from username@host
            if '@' in full_username:
                self.ssh_host = full_username.split('@')[1]
        
        # Extract port (-p PORT)
        port_match = re.search(r'-p\s+(\d+)', self.ssh_command)
        if port_match:
            self.ssh_port = int(port_match.group(1))
        
        # Extract local port and proxy port (-L LOCAL:adb-proxy:REMOTE)
        port_forward_match = re.search(r'-L\s+(\d+):adb-proxy:(\d+)', self.ssh_command)
        if port_forward_match:
            self.local_adb_port = int(port_forward_match.group(1))
            self.adb_proxy_port = int(port_forward_match.group(2))
        
        return True
    
    def __repr__(self):
        return f'<BotConfig User:{self.user_id}>'


class BotTimer(db.Model):
    """BotTimer Model - Track when bot was started/stopped"""
    
    __tablename__ = 'bot_timers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    stopped_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('bot_timers', lazy='dynamic'))
    
    @property
    def duration_minutes(self):
        """Get duration in minutes"""
        if self.stopped_at:
            delta = self.stopped_at - self.started_at
        else:
            delta = datetime.utcnow() - self.started_at
        return int(delta.total_seconds() / 60)
    
    @property
    def is_running(self):
        """Check if timer is still running"""
        return self.stopped_at is None
    
    def __repr__(self):
        return f'<BotTimer User:{self.user_id} Started:{self.started_at}>'


class BotLog(db.Model):
    """BotLog Model - Log bot actions and events"""
    
    __tablename__ = 'bot_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    level = db.Column(db.String(20), default='info')  # info, warning, error, success
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('bot_logs', lazy='dynamic'))
    
    @staticmethod
    def add_log(user_id, level, message):
        """Helper method to add log entry"""
        log = BotLog(user_id=user_id, level=level, message=message)
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self):
        return f'<BotLog {self.level}: {self.message[:50]}>'