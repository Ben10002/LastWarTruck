from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

# Import all models
from .user import User
from .license import License
from .subscription import Subscription
from .bot_config import BotConfig, BotTimer, BotLog
from .bot_schedule import BotSchedule