import os
from flask import Flask, render_template, redirect, url_for
from flask_session import Session
from config import config
from models import db, login_manager
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, time as dt_time
import atexit


def create_app(config_name=None):
    """Application Factory"""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize Flask-Session
    Session(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.session_protection = 'strong'
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Register Blueprints
    from routes import auth, admin, dashboard
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(dashboard.bp)
    
    # Home Route
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))
    
    # Error Handlers
    @app.errorhandler(404)
    def not_found(error):
        return "404 - Page not found", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return "500 - Internal server error", 500
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        from models.user import User
        admin = User.query.filter_by(email=app.config['ADMIN_EMAIL']).first()
        if not admin:
            admin = User(
                email=app.config['ADMIN_EMAIL'],
                is_admin=True
            )
            admin.set_password('admin123')  # CHANGE THIS!
            db.session.add(admin)
            db.session.commit()
            print(f"Admin user created: {app.config['ADMIN_EMAIL']} / admin123")
    
    # Initialize APScheduler
    scheduler = BackgroundScheduler()
    
    # Add job to check schedules every minute
    from scheduler_tasks import check_schedules
    scheduler.add_job(
        func=check_schedules,
        trigger=CronTrigger(second=0),  # Run at the start of every minute
        id='check_schedules',
        name='Check bot schedules',
        replace_existing=True
    )
    
    # Start scheduler
    scheduler.start()
    print("[SCHEDULER] Background scheduler started")
    
    # Shutdown scheduler on app exit
    atexit.register(lambda: scheduler.shutdown())
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)