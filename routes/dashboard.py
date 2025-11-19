from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from models import db
from models.user import User
from models.license import License
from models.subscription import Subscription
from models.bot_config import BotConfig, BotLog
from datetime import datetime

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
        return redirect(url_for('dashboard.index', error='empty'))
    
    # Find license
    license = License.query.filter_by(key=license_key).first()
    
    if not license:
        return redirect(url_for('dashboard.index', error='invalid'))
    
    if license.is_redeemed:
        return redirect(url_for('dashboard.index', error='redeemed'))
    
    # Redeem license
    if license.redeem(user):
        db.session.commit()
        return redirect(url_for('dashboard.index', success='true', days=license.duration_days))
    else:
        return redirect(url_for('dashboard.index', error='failed'))


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
    
    # Start bot (will implement later)
    bot_config.is_running = True
    bot_config.last_started = datetime.utcnow()
    db.session.commit()
    
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
    
    # Stop bot (will implement later)
    bot_config.is_running = False
    bot_config.last_stopped = datetime.utcnow()
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
        # Update user-configurable settings only
        bot_config.interval_minutes = int(request.form.get('interval_minutes', 60))
        bot_config.share_alliance = request.form.get('share_alliance') == 'on'
        bot_config.share_world = request.form.get('share_world') == 'on'
        bot_config.min_strength = int(request.form.get('min_strength', 1000000))
        bot_config.max_strength = int(request.form.get('max_strength', 10000000))
        bot_config.server_restriction = request.form.get('server_restriction', 'none')
        bot_config.language = request.form.get('language', 'en')
        
        db.session.commit()
        
        BotLog.add_log(user.id, 'info', 'Bot configuration updated')
        
        return redirect(url_for('dashboard.index', success='config_saved'))
    
    return render_template('user/bot_configure.html', bot_config=bot_config, user=user)