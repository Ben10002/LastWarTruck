from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from flask import abort
from models import db
from models.user import User
from models.license import License
from models.subscription import Subscription

bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_licenses = License.query.count()
    available_licenses = License.query.filter_by(is_redeemed=False).count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_licenses=total_licenses,
                         available_licenses=available_licenses)


@bp.route('/licenses')
@login_required
@admin_required
def licenses():
    """View and manage licenses"""
    licenses = License.query.order_by(License.created_at.desc()).all()
    return render_template('admin/licenses.html', licenses=licenses)


@bp.route('/licenses/generate', methods=['POST'])
@login_required
@admin_required
def generate_license():
    """Generate new license key"""
    duration = request.form.get('duration', type=int)
    
    if not duration or duration < 1:
        flash('Invalid duration specified.', 'error')
        return redirect(url_for('admin.licenses'))
    
    # Generate unique key
    while True:
        key = License.generate_key()
        if not License.query.filter_by(key=key).first():
            break
    
    # Create license
    license = License(
        key=key,
        duration_days=duration
    )
    
    db.session.add(license)
    db.session.commit()
    
    flash(f'License key generated: {key} ({duration} days)', 'success')
    return redirect(url_for('admin.licenses'))


@bp.route('/licenses/delete/<int:license_id>', methods=['POST'])
@login_required
@admin_required
def delete_license(license_id):
    """Delete a license key"""
    license = License.query.get_or_404(license_id)
    
    if license.is_redeemed:
        flash('Cannot delete redeemed license.', 'error')
        return redirect(url_for('admin.licenses'))
    
    db.session.delete(license)
    db.session.commit()
    
    flash('License deleted successfully.', 'success')
    return redirect(url_for('admin.licenses'))


@bp.route('/users')
@login_required
@admin_required
def users():
    """View and manage users"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@bp.route('/users/toggle/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user(user_id):
    """Suspend/Activate user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot modify admin user.', 'error')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'suspended'
    flash(f'User {user.email} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    
    if user.is_admin:
        flash('Cannot delete admin user.', 'error')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.email} has been deleted.', 'success')
    return redirect(url_for('admin.users'))