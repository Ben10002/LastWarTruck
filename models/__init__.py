from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

# Import all models here
from .user import User
from .subscription import Subscription, LicenseKey
from .bot_config import BotConfig, BotTimer, BotLog

__all__ = ['db', 'login_manager', 'User', 'Subscription', 'LicenseKey', 'BotConfig', 'BotTimer', 'BotLog']