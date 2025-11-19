from flask import Blueprint, render_template
from flask_login import login_required, current_user
from functools import wraps
from flask import abort

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
# @login_required
# @admin_required
def dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html')
```