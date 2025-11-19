from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from datetime import datetime
from models import db
from models.user import User
from models.license import License
from models.subscription import Subscription
from models.bot_config import BotConfig, BotLog, BotTimer
from models.bot_schedule import BotSchedule

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = request.cookies.get('user_id') or session.get('user_id')
        
        if not user_id:
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
def index():
    """User dashboard"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Get user's subscription
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    
    # Get user's redeemed licenses
    licenses = License.query.filter_by(user_id=user.id).order_by(License.redeemed_at.desc()).all()
    
    # Get or create bot config
    bot_config = BotConfig.query.filter_by(user_id=user.id).first()
    if not bot_config:
        bot_config = BotConfig(user_id=user.id)
        db.session.add(bot_config)
        db.session.commit()
    
    # Get recent bot logs
    bot_logs = BotLog.get_recent_logs(user.id, limit=10)
    
    return render_template('user/dashboard.html', 
                         user=user,
                         subscription=subscription,
                         licenses=licenses,
                         bot_config=bot_config,
                         bot_logs=bot_logs)


@bp.route('/redeem', methods=['POST'])
@login_required
def redeem_license():
    """Redeem a license key"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    license_key = request.form.get('license_key', '').strip().upper()
    
    if not license_key:
        return redirect(url_for('dashboard.licenses', error='empty'))
    
    # Find license
    license = License.query.filter_by(key=license_key).first()
    
    if not license:
        return redirect(url_for('dashboard.licenses', error='invalid'))
    
    if license.is_redeemed:
        return redirect(url_for('dashboard.licenses', error='redeemed'))
    
    # Redeem license
    if license.redeem(user):
        db.session.commit()
        return redirect(url_for('dashboard.licenses', success='true', days=license.duration_days))
    else:
        return redirect(url_for('dashboard.licenses', error='failed'))


@bp.route('/bot/start', methods=['POST'])
@login_required
def start_bot():
    """Start the bot"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Check if user has active subscription
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    if not subscription or not subscription.is_active:
        return redirect(url_for('dashboard.index', error='no_subscription'))
    
    # Get bot config
    bot_config = BotConfig.query.filter_by(user_id=user.id).first()
    
    if not bot_config or not bot_config.is_configured:
        return redirect(url_for('dashboard.index', error='not_configured'))
    
    if bot_config.is_running:
        return redirect(url_for('dashboard.index', error='already_running'))
    
    # Start bot worker in background thread
    import threading
    from bot_worker import VMOSCloudBot
    from flask import current_app
    
    def run_bot():
        # Push app context for this thread
        with current_app.app_context():
            bot = VMOSCloudBot(user.id)
            if bot.start():
                bot.run()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    BotLog.add_log(user.id, 'info', 'Bot started')
    
    return redirect(url_for('dashboard.index', success='bot_started'))


@bp.route('/bot/stop', methods=['POST'])
@login_required
def stop_bot():
    """Stop the bot"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Get bot config
    bot_config = BotConfig.query.filter_by(user_id=user.id).first()
    
    if not bot_config or not bot_config.is_running:
        return redirect(url_for('dashboard.index', error='not_running'))
    
    # Stop the active timer
    active_timer = BotTimer.query.filter_by(user_id=user.id, stopped_at=None).first()
    if active_timer:
        active_timer.stopped_at = datetime.utcnow()
        db.session.commit()
    
    BotLog.add_log(user.id, 'info', 'Bot stopped')
    
    return redirect(url_for('dashboard.index', success='bot_stopped'))


@bp.route('/bot/configure', methods=['GET', 'POST'])
@login_required
def configure_bot():
    """Configure bot settings"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Get or create bot config
    bot_config = BotConfig.query.filter_by(user_id=user.id).first()
    if not bot_config:
        bot_config = BotConfig(user_id=user.id)
        db.session.add(bot_config)
        db.session.commit()
    
    if request.method == 'POST':
        # Sharing settings - mutually exclusive
        share_alliance = request.form.get('share_alliance') == 'on'
        share_world = request.form.get('share_world') == 'on'
        
        # Only one can be true
        if share_alliance and share_world:
            return redirect(url_for('dashboard.configure_bot', error='both_share'))
        
        bot_config.share_alliance = share_alliance
        bot_config.share_world = share_world
        
        # Truck strength limit (in millions)
        bot_config.truck_strength = int(request.form.get('truck_strength', 30))
        
        # Server restriction
        bot_config.server_restriction_enabled = request.form.get('server_restriction_enabled') == 'on'
        if bot_config.server_restriction_enabled:
            bot_config.server_restriction_value = int(request.form.get('server_restriction_value', 0))
        else:
            bot_config.server_restriction_value = None
        
        # Running timer
        bot_config.running_timer_enabled = request.form.get('running_timer_enabled') == 'on'
        if bot_config.running_timer_enabled:
            bot_config.running_timer_minutes = int(request.form.get('running_timer_minutes', 60))
        else:
            bot_config.running_timer_minutes = 60  # Keep default for when enabled later
        
        # Remember trucks
        bot_config.remember_trucks_hours = int(request.form.get('remember_trucks_hours', 1))
        
        db.session.commit()
        
        BotLog.add_log(user.id, 'info', 'Bot configuration updated')
        
        return redirect(url_for('dashboard.index', success='config_saved'))
    
    return render_template('user/bot_configure.html', bot_config=bot_config, user=user)


@bp.route('/licenses')
@login_required
def licenses():
    """License management page"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Get user's subscription
    subscription = Subscription.query.filter_by(user_id=user.id).first()
    
    # Get user's redeemed licenses
    licenses = License.query.filter_by(user_id=user.id).order_by(License.redeemed_at.desc()).all()
    
    return render_template('user/licenses.html', 
                         user=user,
                         subscription=subscription,
                         licenses=licenses)


@bp.route('/schedule')
@login_required
def schedule():
    """Bot scheduler page"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Get user's schedules
    schedules = BotSchedule.query.filter_by(user_id=user.id).order_by(BotSchedule.scheduled_date, BotSchedule.start_time).all()
    
    # Get bot config for defaults
    bot_config = BotConfig.query.filter_by(user_id=user.id).first()
    if not bot_config:
        bot_config = BotConfig(user_id=user.id)
        db.session.add(bot_config)
        db.session.commit()
    
    # Get today's date for min attribute
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    
    return render_template('user/schedule.html', 
                         user=user,
                         schedules=schedules,
                         bot_config=bot_config,
                         today=today)

@bp.route('/schedule/add', methods=['POST'])
@login_required
def add_schedule():
    """Add a new schedule"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    # Get form data
    name = request.form.get('name', '').strip()
    scheduled_date_str = request.form.get('scheduled_date')
    start_time_str = request.form.get('start_time')
    end_time_str = request.form.get('end_time')
    
    # Validate
    if not name or not start_time_str or not end_time_str:
        return redirect(url_for('dashboard.schedule', error='missing_fields'))
    
    # Parse times
    from datetime import time as dt_time, date as dt_date
    start_time = dt_time.fromisoformat(start_time_str)
    end_time = dt_time.fromisoformat(end_time_str)
    
    # Check if end time is after start time
    if end_time <= start_time:
        return redirect(url_for('dashboard.schedule', error='invalid_time'))
    
    # Parse date (empty = recurring daily)
    scheduled_date = dt_date.fromisoformat(scheduled_date_str) if scheduled_date_str else None
    
    # Check if date is in the past
    if scheduled_date and scheduled_date < dt_date.today():
        return redirect(url_for('dashboard.schedule', error='past_date'))
    
    # Create new schedule
    new_schedule = BotSchedule(
        user_id=user.id,
        name=name,
        scheduled_date=scheduled_date,
        start_time=start_time,
        end_time=end_time,
        share_alliance=request.form.get('share_alliance') == 'on',
        share_world=request.form.get('share_world') == 'on',
        truck_strength=int(request.form.get('truck_strength', 30)),
        server_restriction_enabled=request.form.get('server_restriction_enabled') == 'on',
        server_restriction_value=int(request.form.get('server_restriction_value')) if request.form.get('server_restriction_value') else None
    )
    
    # Check for overlaps
    existing_schedules = BotSchedule.query.filter_by(user_id=user.id, is_active=True).all()
    for schedule in existing_schedules:
        if new_schedule.overlaps_with(schedule):
            return redirect(url_for('dashboard.schedule', error='overlap', conflict_name=schedule.name))
    
    db.session.add(new_schedule)
    db.session.commit()
    
    BotLog.add_log(user.id, 'info', f'Schedule "{name}" created')
    
    return redirect(url_for('dashboard.schedule', success='added'))


@bp.route('/schedule/delete/<int:schedule_id>', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    """Delete a schedule"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    schedule = BotSchedule.query.get_or_404(schedule_id)
    
    # Check ownership
    if schedule.user_id != user.id:
        abort(403)
    
    schedule_name = schedule.name
    db.session.delete(schedule)
    db.session.commit()
    
    BotLog.add_log(user.id, 'info', f'Schedule "{schedule_name}" deleted')
    
    return redirect(url_for('dashboard.schedule', success='deleted'))


@bp.route('/schedule/toggle/<int:schedule_id>', methods=['POST'])
@login_required
def toggle_schedule(schedule_id):
    """Toggle schedule active/inactive"""
    user_id = request.cookies.get('user_id') or session.get('user_id')
    user = User.query.get_or_404(int(user_id))
    
    schedule = BotSchedule.query.get_or_404(schedule_id)
    
    # Check ownership
    if schedule.user_id != user.id:
        abort(403)
    
    schedule.is_active = not schedule.is_active
    db.session.commit()
    
    status = 'activated' if schedule.is_active else 'deactivated'
    BotLog.add_log(user.id, 'info', f'Schedule "{schedule.name}" {status}')
    
    return redirect(url_for('dashboard.schedule', success='toggled'))