from datetime import datetime
from . import db


class BotConfig(db.Model):
    """BotConfig Model - Bot & VMOSCloud Einstellungen pro User"""
    
    __tablename__ = 'bot_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # VMOSCloud SSH Verbindung
    ssh_host = db.Column(db.String(255), nullable=True)
    ssh_port = db.Column(db.Integer, default=22)
    ssh_user = db.Column(db.String(100), nullable=True)
    ssh_pass = db.Column(db.String(255), nullable=True)  # Encrypted speichern in Production!
    adb_port = db.Column(db.Integer, default=5555)
    
    # Screen Settings
    screen_width = db.Column(db.Integer, default=720)
    screen_height = db.Column(db.Integer, default=1280)
    
    # Bot Settings
    share_mode = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(2), default='de')  # 'de' oder 'en'
    
    # Bot Status
    is_running = db.Column(db.Boolean, default=False)
    last_started = db.Column(db.DateTime, nullable=True)
    last_stopped = db.Column(db.DateTime, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def is_configured(self):
        """Prüfe ob Bot vollständig konfiguriert ist"""
        return all([
            self.ssh_host,
            self.ssh_user,
            self.ssh_pass
        ])
    
    def to_dict(self):
        """Konvertiere zu Dictionary für Bot"""
        return {
            'ssh_host': self.ssh_host,
            'ssh_port': self.ssh_port,
            'ssh_user': self.ssh_user,
            'ssh_pass': self.ssh_pass,
            'adb_port': self.adb_port,
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'share_mode': self.share_mode,
            'language': self.language
        }
    
    def __repr__(self):
        return f'<BotConfig user_id={self.user_id} configured={self.is_configured}>'


class BotTimer(db.Model):
    """BotTimer Model - Persistente Timer pro User"""
    
    __tablename__ = 'bot_timers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timer_name = db.Column(db.String(50), nullable=False)  # z.B. 'lkw_1', 'lkw_2', etc.
    next_run = db.Column(db.DateTime, nullable=False)
    interval_seconds = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint: Ein User kann nur einen Timer mit gleichem Namen haben
    __table_args__ = (
        db.UniqueConstraint('user_id', 'timer_name', name='unique_user_timer'),
    )
    
    @property
    def is_ready(self):
        """Prüfe ob Timer bereit zum Ausführen ist"""
        return datetime.utcnow() >= self.next_run and self.is_active
    
    def reset(self):
        """Setze Timer zurück (nächster Run = jetzt + interval)"""
        from datetime import timedelta
        self.next_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<BotTimer {self.timer_name} next={self.next_run}>'


class BotLog(db.Model):
    """BotLog Model - Log-Einträge pro User"""
    
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
        """Füge neuen Log-Eintrag hinzu"""
        log = BotLog(
            user_id=user_id,
            log_type=log_type,
            message=message
        )
        db.session.add(log)
        db.session.commit()
    
    @staticmethod
    def get_recent_logs(user_id, limit=50):
        """Hole die neuesten Logs für einen User"""
        return BotLog.query.filter_by(user_id=user_id)\
                          .order_by(BotLog.created_at.desc())\
                          .limit(limit)\
                          .all()
    
    @staticmethod
    def clear_old_logs(days=7):
        """Lösche Logs die älter als X Tage sind"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        BotLog.query.filter(BotLog.created_at < cutoff).delete()
        db.session.commit()