import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class Config:
    """Base configuration for the application"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///lkw_bot.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Admin
    ADMIN_EMAIL = 'leerzeichen183@gmail.com'  # Change this later
    
    # Bot
    BOT_DEFAULT_SCREEN_WIDTH = 720
    BOT_DEFAULT_SCREEN_HEIGHT = 1280
    MAINTENANCE_MODE = False  # Global maintenance mode
    
    # Subscription
    DEFAULT_SUBSCRIPTION_DAYS = 30
    MONTHLY_PRICE = 15.0  # Euro


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # HTTPS required


# Config auswählen basierend auf Environment Variable
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}