"""
Background scheduler tasks for bot automation
"""
from datetime import datetime, time as dt_time
import pytz  # Neu hinzufügen
from models import db
from models.bot_config import BotConfig, BotTimer
from models.bot_schedule import BotSchedule
from models.user import User
import threading

# Deutsche Zeitzone
TIMEZONE = pytz.timezone('Europe/Berlin')


def check_schedules():
    """
    Check if any schedules need to be started or stopped
    Runs every minute
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Nutze deutsche Zeit
        now = datetime.now(TIMEZONE)
        current_time = now.time()
        current_date = now.date()
        
        print(f"[SCHEDULER] Checking schedules at {now.strftime('%Y-%m-%d %H:%M:%S')} (Berlin)")
        
        # Get all active schedules
        schedules = BotSchedule.query.filter_by(is_active=True).all()
        
        for schedule in schedules:
            user = User.query.get(schedule.user_id)
            if not user:
                continue
            
            bot_config = BotConfig.query.filter_by(user_id=user.id).first()
            if not bot_config:
                continue
            
            # Check if schedule matches current time (within 1 minute window)
            should_run = False
            
            # If specific date is set, check if it matches
            if schedule.scheduled_date:
                if schedule.scheduled_date != current_date:
                    continue  # Wrong date
            
            # Check if we're within the start time window (±1 minute)
            start_hour = schedule.start_time.hour
            start_minute = schedule.start_time.minute
            current_hour = current_time.hour
            current_minute = current_time.minute
            
            # Check for start time
            if (start_hour == current_hour and 
                abs(start_minute - current_minute) <= 1 and
                not bot_config.is_running):
                
                print(f"[SCHEDULER] Starting bot for user {user.email} (schedule: {schedule.name})")
                
                # Apply schedule settings to bot config
                bot_config.share_alliance = schedule.share_alliance
                bot_config.share_world = schedule.share_world
                bot_config.truck_strength = schedule.truck_strength
                bot_config.server_restriction_enabled = schedule.server_restriction_enabled
                bot_config.server_restriction_value = schedule.server_restriction_value
                db.session.commit()
                
                # Start bot
                start_bot_for_user(user.id)
            
            # Check for end time
            end_hour = schedule.end_time.hour
            end_minute = schedule.end_time.minute
            
            if (end_hour == current_hour and 
                abs(end_minute - current_minute) <= 1 and
                bot_config.is_running):
                
                print(f"[SCHEDULER] Stopping bot for user {user.email} (schedule: {schedule.name})")
                
                # Stop bot
                stop_bot_for_user(user.id)


def start_bot_for_user(user_id):
    """Start bot for a specific user"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Create new timer
        new_timer = BotTimer(user_id=user_id)
        db.session.add(new_timer)
        db.session.commit()
        
        # Start bot in background thread
        from bot_worker import VMOSCloudBot
        
        def run_bot():
            with app.app_context():
                try:
                    bot = VMOSCloudBot(user_id)
                    if bot.start():
                        bot.run()
                except Exception as e:
                    print(f"[SCHEDULER] Bot thread error: {e}")
        
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()


def stop_bot_for_user(user_id):
    """Stop bot for a specific user"""
    from app import create_app
    app = create_app()
    
    with app.app_context():
        # Stop the active timer
        active_timer = BotTimer.query.filter_by(user_id=user_id, stopped_at=None).first()
        if active_timer:
            active_timer.stopped_at = datetime.utcnow()
            db.session.commit()