from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort
from functools import wraps
from models import db
from models.user import User
from models.license import License
from models.subscription import Subscription

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
    
    return render_template('user/dashboard.html', 
                         user=user,
                         subscription=subscription,
                         licenses=licenses)


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